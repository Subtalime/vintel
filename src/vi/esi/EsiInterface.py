import logging
from esipy.utils import generate_code_verifier
from esipy import EsiClient, EsiApp, EsiSecurity
from esipy.security import APIException
from esipy.events import AFTER_TOKEN_REFRESH
from esiconfig import EsiConfig
from pyswagger.io import Response, CaseInsensitiveDict
import datetime
import json
import ast
from urllib.parse import urlparse, parse_qs
import vi.version
import webbrowser
import threading
from vi.cache.cache import Cache
from http.server import HTTPServer, BaseHTTPRequestHandler

secretKey = None
esiLoading = False
def _after_token_refresh(access_token, refresh_token, expires_in, **kwargs):
    logging.info("TOKEN We got new token: %s" % access_token)
    logging.info("TOKEN refresh token used: %s" % refresh_token)
    logging.info("TOKEN Expires in %d" % expires_in)


class EsiInterface:
    instance = None
    # make it a Singleton
    class __OnceOnly:
        def __init__(self, enablecache: bool = True):
            global secretKey
            global esiLoading
            if esiLoading:
                while esiLoading is not "complete":
                    pass
                return
            esiLoading = True
            self.caching = enablecache
            logging.debug("Creating ESI access")
            self.authenticated = False
            self.esiConfig = EsiConfig()
            self.server = None
            self.headers = {'User-Agent': "{} Intel Management Tool".format(vi.version.PROGNAME)}
            self.codeverifier = generate_code_verifier()
            try:
                # this uses PKCE (pixie) authorisation with ESI
                self.security = EsiSecurity(
                    # The application (matching ESI_CLIENT_ID) must have the same Callback configured!
                    redirect_uri=self.esiConfig.ESI_CALLBACK,
                    client_id=self.esiConfig.ESI_CLIENT_ID,
                    code_verifier=self.codeverifier,
                    headers=self.headers
                )

                # this authentication can be used with all ESI calls
                self.esiClient = EsiClient(security=self.security,
                                           retry_requests=True,
                                           headers=self.headers
                                           )
                self.apiInfo = None
                tokenKey = None
                cacheToken = Cache().getFromCache("esi_token")
                if cacheToken:
                    tokenKey = json.loads(cacheToken)
                while not self.apiInfo:
                    try:
                        if secretKey:
                            self.esiConfig.setSecretKey(secretKey)
                            secretKey = None
                            self.tokens = self.security.auth(self.esiConfig.getSecretKey())
                            self.apiInfo = self.security.verify()
                            # store the Token
                            Cache().putIntoCache("esi_token", json.dumps(self.tokens))
                        elif tokenKey:
                            self.security.update_token(tokenKey)
                            self.apiInfo = self.security.refresh()
                        else:
                            self.waitForSecretKey()
                    except APIException as e:
                        logging.error("EsiAPI Error", e)
                        self.waitForSecretKey()
                    except AttributeError as e:
                        logging.error("EsiAttribute Error", e)
                        self.waitForSecretKey()
                    except Exception as e:
                        logging.error("Some unexpected error in Esi", e)

                logging.debug("ESI loading Swagger...")
                # outputs a load of data in Debug
                oldSetting = logging.getLogger().getEffectiveLevel()
                logging.getLogger().setLevel(logging.ERROR)
                # self.esiApp = EsiApp()
                self.esiApp = EsiApp().get_latest_swagger
                # Reset logging to old level
                logging.getLogger().setLevel(oldSetting)
                logging.debug("ESI loading Swagger...complete")
                self.authenticated = True
                logging.debug("Finished authorizing with ESI")
            except Exception as e:
                logging.critical("Error authenticating with ESI", e)
                exit(-1)
            esiLoading = "complete"

        def waitForSecretKey(self):
            global secretKey
            redirected = False
            while not secretKey:
                if not self.server:
                    self.server = self.EsiWebServer(self.esiConfig)
                    self.server.start()
                if not redirected:
                    ssoUri = self.security.get_auth_uri(
                        state="Authentication for {}".format(vi.version.PROGNAME),
                        scopes=None
                    )
                    webbrowser.open(ssoUri)
                    redirected = True
            if self.server:
                self.server.stop()
                self.server = None

        class EsiWebServer(object):
            def __init__(self, esiConfigInstance: EsiConfig):
                self.esiConfig = esiConfigInstance
                self.httpd = HTTPServer((self.esiConfig.HOST, self.esiConfig.PORT), self.EsiHTTPRequestHandler)
                self.server_thread = threading.Thread(target=self.httpd.serve_forever)
                self.server_thread.daemon = True

            def start(self):
                self.server_thread.start()

            def stop(self):
                self.httpd.shutdown()
                self.httpd.server_close()

            class EsiHTTPRequestHandler(BaseHTTPRequestHandler):
                def do_GET(self):
                    logging.debug("Got a \"GET\" request: {}".format(self.requestline))
                    self.send_response(200)
                    self.end_headers()
                    try:
                        urlobjects = urlparse(self.requestline)
                        thisquery = parse_qs(urlobjects.query)
                        if thisquery['code']:
                            global secretKey
                            secretKey = thisquery['code'][0]
                            self.wfile.write(b"You have verified your account on ESI. You can now close this window")
                    except Exception as e:
                        logging.error("Unexpected response: {}".format(self.requestline))
                        self.wfile.write(b"I don't know what you are on about")

        def __str__(self):
            return repr(self)

    def __init__(self, useCaching: bool = True):
        if not EsiInterface.instance:
            self.caching = useCaching
            AFTER_TOKEN_REFRESH.add_receiver(_after_token_refresh)
            EsiInterface.instance = EsiInterface.__OnceOnly(useCaching)

    def __getattr__(self, name):
        return getattr(self.instance, name)

    # def _cacheVar(self, function: str, **kwargs):
    #     return "_".join(("esicache", function, for var in kwargs))
    #
    def getCharacter(self, characterId: int) -> Response:
        # Character-Caching is based on EveTime... we want to reload after Eve is back up
        if self.caching:
            cacheKey = "_".join(("esicache", "getcharacter", str(characterId)))
            result = Cache().getFromCache(cacheKey)
            if result:
                return ast.literal_eval(result)
        response = None
        try:
            self.security.verify()
            if not self.authenticated:
                logging.error("ESI not authenticated")
            else:
                # update the Token
                self.esiClient.request()
                op = self.esiApp.op['get_characters_character_id'] (character_id=characterId)
                response = self.esiClient.request(op)
                # format is {"alliance_id": xx, "ancestry_id": xx, "birthday": xx, "bloodline_id": xx, "corporation_id": xx,
                #            "description": xx, "gender": xx, "name": xx, "race_id": xx, "security_status": xx, "title": xx}
                if self.caching:
                    expire_date = response.header.get('Expires')[0]
                    cacheUntil = datetime.datetime.strptime(expire_date, "%a, %d %b %Y %H:%M:%S %Z")
                    diff = cacheUntil - self.currentEveTime()
                    Cache().putIntoCache(cacheKey, str(response), diff.seconds)
                return response
        except Exception as e:
            logging.error("Error retrieving Character {} from ESI".format(characterId), e)
        return None

    def getCorporation(self, corpid: int) -> Response:
        if self.caching:
            cacheKey = "_".join(("esicache", "getcorporation", str(corpid)))
            result = Cache().getFromCache(cacheKey)
            if result:
                return ast.literal_eval(result)
        response = None
        try:
            self.security.verify()
            if not self.authenticated:
                logging.error("ESI not authenticated")
            else:
                op = self.esiApp.op['get_corporations_corporation_id'] (corporation_id=corpid)
                response = self.esiClient.request(op)
                if self.caching:
                    Cache().putIntoCache(cacheKey, str(response))
                # format is {"alliance_id": xx, "ceo_id": xx, "creator_id": xx, "data_founded": xx, "description": xx,
                #            "war_elligible": xx, "url": xx, "ticker": xx, "shares": xx, "name": xx, "member_count": xx,
                #            "home_station_id": xx }
                return response
        except Exception as e:
            logging.error("Error retrieving Corporation {} from ESI".format(corpid), e)
        return None

    def getCorporationHistory(self, characterId: int) -> Response:
        if self.caching:
            cacheKey = "_".join(("esicache", "getcorporationhist", str(characterId)))
            result = Cache().getFromCache(cacheKey)
            if result:
                return ast.literal_eval(result)
        response = None
        try:
            self.security.verify()
            if not self.authenticated:
                logging.error("ESI not authenticated")
            else:
                op = self.esiApp.op['get_characters_character_id_corporationhistory'] (character_id=characterId)
                response = self.esiClient.request(op)
                if self.caching:
                    Cache().putIntoCache(cacheKey, str(response))
                # format is {"corporation_id": xx, "record_id": xx, "start_date": xx},...
                return response
        except Exception as e:
            logging.error("Error retrieving Corporation-History {} from ESI".format(characterId), e)
        return None

    def getCharacterId(self, charname: str, strict: bool=True) -> Response:
        if self.caching:
            cacheKey = "_".join(("esicache", "getcharacterid", charname))
            result = Cache().getFromCache(cacheKey)
            if result:
                return ast.literal_eval(result)
        response = None
        try:
            self.security.verify()
            if not self.authenticated:
                logging.error("ESI not authenticated")
            else:
                op = self.esiApp.op['get_search'] (categories='character', search=charname, strict=strict)
                response = self.esiClient.request(op)
                if self.caching:
                    Cache().putIntoCache(cacheKey, str(response))
                # format is {"character": [xxx,...]}
                return response
        except Exception as e:
            logging.error("Error retrieving Character-ID by Name {} from ESI".format(charname), e)
        return response

    def getCharacterAvatar(self, characterId: int) -> Response:
        if self.caching:
            cacheKey = "_".join(("esicache", "getcharavatar", str(characterId)))
            result = Cache().getFromCache(cacheKey)
            if result:
                return ast.literal_eval(result)
        response = None
        try:
            self.security.verify()
            if not self.authenticated:
                logging.error("ESI not authenticated")
            else:
                op = self.esiApp.op['get_characters_character_id_portrait'] (character_id=characterId)
                response = self.esiClient.request(op)
                if self.caching:
                    Cache().putIntoCache(cacheKey, str(response))
                return response
        except Exception as e:
            logging.error("Error retrieving Character Avatar for ID {} from ESI".format(characterId), e)
        return response

    def getSystemIds(self, namelist: list) -> Response:
        if self.caching:
            cacheKey = "_".join(("esicache", "getsystemids", str(namelist)))
            result = Cache().getFromCache(cacheKey)
            if result:
                return ast.literal_eval(result)
        response = None
        try:
            self.security.verify()
            if not self.authenticated:
                logging.error("ESI not authenticated")
            else:
                self.esiClient.request()
                op = self.esiApp.op['post_universe_ids'] (names=namelist)
                response = self.esiClient.request(op)
                if self.caching:
                    Cache.putIntoCache(cacheKey, str(response))
                # format is [{"name": xx, "id": xx} ...]
                return response
        except Exception as e:
            logging.error("Error retrieving System-IDs for {} from ESI".format(namelist), e)
        return response

    def getSystemNames(self, idlist: list) -> Response:
        if self.caching:
            cacheKey = "_".join(("esicache", "getsystemnames", str(idlist)))
            result = Cache().getFromCache(cacheKey)
            if result:
                return ast.literal_eval(result)
        response = None
        try:
            self.security.verify()
            if not self.authenticated:
                logging.error("ESI not authenticated")
            else:
                op = self.esiApp.op['post_universe_names'] (ids=idlist)
                response = self.esiClient.request(op)
                if self.caching:
                    Cache().putIntoCache(cacheKey, str(response))
                # format is [{"category": xx, "name": xx, "id": xx} ...]
                return response
        except Exception as e:
            logging.error("Error retrieving System-Names for {} from ESI".format(idlist), e)
        return response

    # not caching this
    def getKills(self) -> Response:
        response = None
        try:
            self.security.verify()
            if not self.authenticated:
                logging.error("ESI not authenticated")
            else:
                self.esiClient.request()
                op = self.esiApp.op['get_universe_system_kills']()
                response = self.esiClient.request(op)
                # format is [{"npc_kills": xx, "pod_kills": xx, "ship_kills": xx, ""system_id": xx} ...]
                return response
        except Exception as e:
            logging.error("Error retrieving Kills from ESI", e)
        return response

    # not caching this
    def getJumps(self) -> Response:
        response = None
        try:
            self.security.verify()
            if not self.authenticated:
                logging.error("ESI not authenticated")
            else:
                op = self.esiApp.op['get_universe_system_jumps']()
                response = self.esiClient.request(op)
                # format is [{"ship_jumps": xx, "system_id": xx} ...]
                return response
        except Exception as e:
            logging.error("Error retrieving Jums from ESI", e)
        return response


    def getShipGroups(self) -> Response.data:
        if self.caching:
            cacheKey = "_".join(("esicache", "getshipgroups"))
            result = Cache().getFromCache(cacheKey)
            if result:
                return ast.literal_eval(result)
        response = None
        try:
            self.security.verify()
            if not self.authenticated:
                logging.error("ESI not authenticated")
            else:
                # this will return Groups of type 6 (ship)
                op = self.esiApp.op['get_universe_categories_category_id'](category_id=6)
                response = self.esiClient.request(op)
                if self.caching:
                    Cache().putIntoCache(cacheKey, str(response.data))
                # format is [{"ship_jumps": xx, "system_id": xx} ...]
                return response.data
        except Exception as e:
            logging.error("Error retrieving Ship-Groups from ESI", e)
        return response

    def getShipGroupTypes(self, groupid: int) -> Response.data:
        if self.caching:
            cacheKey = "_".join(("esicache", "getshipgrouptype", str(groupid)))
            result = Cache().getFromCache(cacheKey)
            if result:
                return ast.literal_eval(result)
        response = None
        try:
            self.security.verify()
            if not self.authenticated:
                logging.error("ESI not authenticated")
            else:
                # this will return Groups of type 6 (ship)
                op = self.esiApp.op['get_universe_groups_group_id'](group_id=groupid)
                response = self.esiClient.request(op)
                if self.caching:
                    Cache().putIntoCache(cacheKey, str(response.data))
                # format is [{"ship_jumps": xx, "system_id": xx} ...]
                return response.data
        except Exception as e:
            logging.error("Error retrieving Ship-Group-Types from ESI", e)
        return response

    def getShip(self, shipid: int) -> Response.data:
        if self.caching:
            cacheKey = "_".join(("esicache", "getship", str(shipid)))
            result = Cache().getFromCache(cacheKey)
            if result:
                return ast.literal_eval(result)
        response = None
        try:
            self.security.verify()
            if not self.authenticated:
                logging.error("ESI not authenticated")
            else:
                # this will return Groups of type 6 (ship)
                op = self.esiApp.op['get_universe_types_type_id'](type_id=shipid)
                response = self.esiClient.request(op)
                if self.caching:
                    Cache().putIntoCache(cacheKey, str(response.data))
                # format is [{"ship_jumps": xx, "system_id": xx} ...]
                return response.data
        except Exception as e:
            logging.error("Error retrieving Ship from ESI", e)
        return response

    @property
    def getShipList(self):
        if self.caching:
            cacheKey = "_".join(("esicache", "getshiplist"))
            result = Cache().getFromCache(cacheKey)
            if result:
                return ast.literal_eval(result)
        ships = []
        shipgroup = self.getShipGroups()
        for group in shipgroup['groups']:
            shiptypes = self.getShipGroupTypes(group)
            for ship in shiptypes['types']:
                shipitem = self.getShip(ship)
                ships.append(shipitem)
        Cache().putIntoCache(cacheKey, str(ships), 30 * 24 * 60 * 60)
        return ships

    def currentEveTime(self) -> datetime.datetime:
        """ Returns the current eve-time as a datetime.datetime
        """
        return datetime.datetime.utcnow()

    def secondsTillDowntime(self) -> int:
        """ Return the seconds till the next downtime"""
        now = self.currentEveTime()
        target = now
        if now.hour > 11:
            target = target + datetime.timedelta(1)
        target = datetime.datetime(target.year, target.month, target.day, 11, 0, 0, 0)
        delta = target - now
        return delta.seconds

if __name__ == "__main__":
    def _cacheVar(function: str, *argv):
        l = []
        for a in argv:
            l.append(str(a))
        return "_".join(("esicache", function))+"_".join(str(argv.__repr__()))

    a = _cacheVar("test", 1, "me")
    import requests, datetime
    logging.getLogger().setLevel(logging.DEBUG)
    esi = EsiInterface()

    ships = esi.getShipList

    shipgroup = esi.getShipGroups()
    for group in shipgroup.data['groups']:
        shiptypes = esi.getShipGroupTypes(group)
        for ship in shiptypes.data['types']:
            shipitem = esi.getShip(ship)
            ships.append(shipitem.data)

    res = esi.getSystemNames([95465449, 30000142])

    chari = esi.getCharacterId("Tablot Manzari")
    print("getCharacterId: {}".format(chari.data))
    esi2 = EsiInterface()
    charid = chari.data['character'][0]
    chara = esi.getCharacter(charid)

    character = chara.data# Tablot Manzari
    print("getCharacter: {}".format(character))
    expire_date = chara.header.get('Expires')[0]
    cacheUntil = datetime.datetime.strptime(expire_date, "%a, %d %b %Y %H:%M:%S %Z")

    avatars = esi2.getCharacterAvatar(charid)  # Tablot Manzari
    print("getCharacterAvatar: {}".format(avatars.data))
    imageurl = avatars.data["px64x64"]
    avatar = requests.get(imageurl).content
    corphist = esi.getCorporationHistory(charid)  # Bovril
    print("getCorporationHistory: {}".format(corphist.data))
    corp = esi.getCorporation(character['corporation_id'])  # Bovril
    print("getCorporation: {}".format(corp.data))
    li = ["B-7DFU", "Jita"]
    ids = esi.getSystemIds(li)
    print("getSystemIds: {}".format(ids.data))
    li = []
    sys = ids.data['systems']
    for a in sys:
        li.append(a['id'])
    names = esi.getSystemNames(li)
    print("getSystemNames: {}".format(names.data))
    jump_result = EsiInterface().getJumps()
    print("getJumps :{}".format(jump_result.data))
    jumpData = {}
    for data in jump_result.data:
        jumpData[int(data['system_id'])] = int(data['ship_jumps'])
    kill_result = EsiInterface().getKills()
    print("getKils :{}".format(kill_result.data))

