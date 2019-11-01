import logging
import datetime
import webbrowser
import functools
import threading
import pickle
import vi.version
from http.server import HTTPServer, BaseHTTPRequestHandler
from http.client import HTTPException
from ast import literal_eval
from pyswagger.io import Response
from urllib.parse import urlparse, parse_qs
from esipy import EsiClient, EsiApp, EsiSecurity
from esipy.utils import generate_code_verifier
from esipy.security import APIException
from esipy.events import AFTER_TOKEN_REFRESH
from .esicache import  EsiCache
from .esiconfig import EsiConfig
from .esiconfigdialog import EsiConfigDialog
from vi.cache.cache import Cache

# secretKey = None
# esiLoading = False

lock = threading.Lock()


def _after_token_refresh(access_token, refresh_token, expires_in, **kwargs):
    logging.info("TOKEN We got new token: %s" % access_token)
    logging.info("TOKEN refresh token used: %s" % refresh_token)
    logging.info("TOKEN Expires in %d" % expires_in)


def synchronized(lock):
    """ Synchronisation decorator """

    def wrapper(f):
        @functools.wraps(f)
        def inner_wrapper(*args, **kwargs):
            with lock:
                return f(*args, **kwargs)

        return inner_wrapper

    return wrapper


class EsiInterfaceType(type):
    _instances = {}

    @synchronized(lock)
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(EsiInterfaceType, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


def logrepr(className: type) -> str:
    return str(className).replace("'", "").replace("__main__.", "").replace("<", "").replace(">",
                                                                                             "")


class EsiInterface(metaclass=EsiInterfaceType):
    _instance = None
    secretKey = None
    esiLoading = False

    # make it a Singleton
    class __OnceOnly:
        def __init__(self, enablecache: bool = True):
            # global secretKey
            # global esiLoading
            if EsiInterface.esiLoading:
                while EsiInterface.esiLoading is not "complete":
                    logging.error("Esi already currently being loaded...")
                    pass
                return
            EsiInterface.esiLoading = True
            self.caching = enablecache
            self.logger = logging.getLogger(logrepr(__class__))
            self.logger.setLevel(logging.DEBUG)
            self.logger.debug("Creating ESI access")
            self.authenticated = False
            self.esiConfig = EsiConfig()
            self.server = None
            self.headers = {'User-Agent': "{} Intel Management Tool".format(vi.version.PROGNAME)}
            self.codeverifier = generate_code_verifier()
            try:
                if self.caching:
                    cacheToken = EsiCache().get("esi_clientid")
                    if cacheToken:
                        EsiConfig.ESI_CLIENT_ID = str(cacheToken)
                    cacheToken = EsiCache().get("esi_callback")
                    if cacheToken:
                        EsiConfig.ESI_CALLBACK = str(cacheToken)
                    cacheToken = EsiCache().get("esi_secretkey")
                    if cacheToken:
                        pass
                        # EsiConfig.ESI_SECRET_KEY = str(cacheToken)
                # this uses PKCE (pixie) authorisation with ESI
                while not EsiConfig.ESI_CLIENT_ID:
                    # TODO: look at PyFa to see how they do it...
                    # TODO: until then, we should stop storing the SecretKey
                    with EsiConfigDialog() as inputDia:
                        inputDia.exec()
                        if not inputDia.Accepted == 1:
                            exit(-1)
                        else:
                            if self.caching:
                                EsiCache().set("esi_clientid", EsiConfig.ESI_CLIENT_ID)
                                EsiCache().set("esi_callback", EsiConfig.ESI_CALLBACK)
                                EsiCache().set("esi_secretkey", EsiConfig.ESI_SECRET_KEY)

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
                self.esiApp = None
                tokenKey = None
                refreshKey = None
                if self.caching:
                    tokenKey = EsiCache().get("esi_token")
                    if tokenKey:
                        refreshKey = tokenKey['refresh_token']
                while not self.apiInfo:
                    try:
                        if EsiInterface.secretKey:
                            self.logger.debug("Checking the Secretkey")
                            self.esiConfig.setSecretKey(EsiInterface.secretKey)
                            EsiInterface.secretKey = None
                            self.tokens = self.security.auth(self.esiConfig.getSecretKey())
                            self.apiInfo = self.security.verify()
                            # store the Token
                            if self.caching:
                                EsiCache().set("esi_token", self.tokens)
                            self.logger.debug("Secretkey success")
                        elif refreshKey:
                            self.logger.debug("Checking the Refresh-Token")
                            self.security.update_token({
                                'access_token': '',
                                'expires_in': -1,
                                'refresh_token': refreshKey
                            })
                            refreshKey = None
                            self.apiInfo = self.security.refresh()
                            self.logger.debug("Refreshtoken success")
                        elif tokenKey:
                            self.logger.debug("Checking the Tokenkey")
                            self.security.update_token(tokenKey)
                            tokenKey = None
                            self.apiInfo = self.security.refresh()
                            self.logger.debug("Tokenkey success")
                        else:
                            self.logger.debug("Waiting for Website response of Secretkey")
                            self.waitForSecretKey()
                    except APIException as e:
                        self.logger.error("EsiAPI Error", e)
                        self.waitForSecretKey()
                    except AttributeError as e:
                        self.logger.error("EsiAttribute Error", e)
                        self.waitForSecretKey()
                    except Exception as e:
                        self.logger.error("Some unexpected error in Esi", e)
                        exit(-1)

                self.logger.debug("ESI loading Swagger...")
                # outputs a load of data in Debug
                oldSetting = self.logger.getEffectiveLevel()
                self.logger.setLevel(logging.WARN)
                while not self.esiApp:
                    try:
                        self.esiApp = EsiApp(cache=EsiCache(), cache_time=3 * 86400).get_latest_swagger
                    except (Exception, HTTPException) as e:
                        self.logger.error("Error while retrieving latest Swagger", e)
                        if e.code == 500:
                            EsiCache().invalidateAll()
                            self.logger.exception("ESI-Interface not explicitly instantiated!")
                            exit(-1)

                # Reset logging to old level
                self.logger.setLevel(oldSetting)
                self.logger.debug("ESI loading Swagger...complete")
                self.authenticated = True
                self.logger.debug("Finished authorizing with ESI")
            except Exception as e:
                self.logger.critical("Error authenticating with ESI", e)
                exit(-1)
            EsiInterface.esiLoading = "complete"

        def waitForSecretKey(self):
            # global secretKey
            redirected = False
            while not EsiInterface.secretKey:
                if not self.server:
                    self.server = self.EsiWebServer(self.esiConfig)
                    self.server.start()
                if not redirected:
                    # if SECRET_KEY is stored, call SSO directly
                    if EsiConfig.ESI_SECRET_KEY:
                        # this should be sent to ESI/verify
                        self.security.verify(
                            {
                                'client_hash': EsiConfig.ESI_SECRET_KEY
                            }
                        )
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
                self.httpd = HTTPServer((self.esiConfig.HOST, self.esiConfig.PORT),
                                        self.EsiHTTPRequestHandler)
                self.server_thread = threading.Thread(target=self.httpd.serve_forever)
                self.server_thread.daemon = True

            def start(self):
                self.server_thread.start()

            def stop(self):
                self.httpd.shutdown()
                self.httpd.server_close()

            class EsiHTTPRequestHandler(BaseHTTPRequestHandler):
                def __init__(self, *args, **kwargs):
                    self.logger = logging.getLogger(logrepr(__class__))
                    super().__init__(*args, **kwargs)

                def do_GET(self):
                    self.logger.debug("Got a \"GET\" request: {}".format(self.requestline))
                    self.send_response(200)
                    self.end_headers()
                    try:
                        urlobjects = urlparse(self.requestline)
                        thisquery = parse_qs(urlobjects.query)
                        if thisquery['code']:
                            # store temporary Secretkey
                            EsiInterface.secretKey = thisquery['code'][0]
                            self.wfile.write(
                                b"You have verified your account on ESI. You can now close this window")
                    except Exception as e:
                        self.logger.error("Unexpected response: %s: %r", self.requestline, e)
                        self.wfile.write(b"I don't know what you are on about")

        def __str__(self):
            return repr(self)

    def __init__(self, useCaching: bool = True):
        if not EsiInterface._instance:
            self.caching = useCaching

            self.logger = logging.getLogger(logrepr(__class__))
            self.logger.setLevel(logging.ERROR)
            AFTER_TOKEN_REFRESH.add_receiver(_after_token_refresh)
            EsiInterface._instance = EsiInterface.__OnceOnly(enablecache=self.caching)

    def __getattr__(self, name):
        return getattr(self._instance, name)


    def calcExpiry(self, expireDate: str) -> datetime.datetime:
        cache_until = datetime.datetime.strptime(expireDate, "%a, %d %b %Y %H:%M:%S %Z")
        diff = cache_until - self.currentEveTime()
        return diff

    def calcExpiryResponse(self, resp: Response) -> datetime.datetime:
        return self.calcExpiry(resp.header.get('Expires')[0])

    @staticmethod
    def _copyModel(self, data) -> dict:
        retval = {}
        for key, val in data.items():
            retval[key] = val
        return retval

    def getCharacter(self, characterId: int) -> Response.data:
        # Character-Caching is based on EveTime... we want to reload after Eve is back up
        response = None
        if self.caching:
            cacheKey = "_".join(("esicache", "getcharacter", str(characterId)))
            result = Cache().getFromCache(cacheKey)
            if result:
                try:
                    response = pickle.loads(result)
                    # response = literal_eval(result)
                except Exception as e:
                    Cache().delFromCache(cacheKey)
                    # logging.error("Unable to parse Cache-Result")
                    pass
        if not response:
            try:
                op = self.esiApp.op['get_characters_character_id'](character_id=characterId)
                response = self.esiClient.request(op)
                # format is {"alliance_id": xx, "ancestry_id": xx, "birthday": xx, "bloodline_id": xx, "corporation_id": xx,
                #            "description": xx, "gender": xx, "name": xx, "race_id": xx, "security_status": xx, "title": xx}
                if response:
                    expiry = self.calcExpiry(response.header.get('Expires')[0])
                    response = self._copyModel(response.data)
                    if self.caching:
                        Cache().putIntoCache(cacheKey, pickle.dumps(response), expiry.seconds)
            except Exception as e:
                if self.caching:
                    Cache().delFromCache(cacheKey)
                self.logger.error("Error retrieving Character \"%d\" from ESI: %r", characterId, e)
        return response

    def getCorporation(self, corpid: int) -> Response.data:
        response = None
        try:
            if self.caching:
                cacheKey = "_".join(("esicache", "getcorporation", str(corpid)))
                result = Cache().getFromCache(cacheKey)
                if result:
                    response = literal_eval(result)
            if not response:
                op = self.esiApp.op['get_corporations_corporation_id'](corporation_id=corpid)
                response = self.esiClient.request(op)
                if response:
                    response = response.data
                    if self.caching:
                        Cache().putIntoCache(cacheKey, str(response))
                # format is {"alliance_id": xx, "ceo_id": xx, "creator_id": xx, "data_founded": xx, "description": xx,
                #            "war_elligible": xx, "url": xx, "ticker": xx, "shares": xx, "name": xx, "member_count": xx,
                #            "home_station_id": xx }
        except Exception as e:
            self.logger.error("Error retrieving Corporation \"%d\" from ESI: %r", corpid, e)
            if self.caching:
                Cache().delFromCache(cacheKey)
        return response

    def getCorporationHistory(self, characterId: int) -> Response.data:
        response = None
        try:
            if self.caching:
                cacheKey = "_".join(("esicache", "getcorporationhist", str(characterId)))
                result = Cache().getFromCache(cacheKey)
                if result:
                    response = literal_eval(result)
            if not response:
                op = self.esiApp.op['get_characters_character_id_corporationhistory'](
                    character_id=characterId)
                response = self.esiClient.request(op)
                if response:
                    response = response.data
                    if self.caching:
                        Cache().putIntoCache(cacheKey, str(response))
                    # format is {"corporation_id": xx, "record_id": xx, "start_date": xx},...
        except Exception as e:
            self.logger.error(
                "Error retrieving Corporation-History for Character \"%d\" from ESI: %r", characterId, e)
            if self.caching:
                Cache().delFromCache(cacheKey)
        return response

    def getCharacterId(self, charname: str, strict: bool = True) -> Response.data:
        response = None
        try:
            cacheKey = "_".join(("esicache", "getcharacterid", "0" if not strict else "1", charname))
            if self.caching:
                result = Cache().getFromCache(cacheKey)
                if result:
                    response = literal_eval(result)
            if not response:
                op = self.esiApp.op['get_search'](categories='character', search=charname,
                                                  strict=strict)
                response = self.esiClient.request(op)
                # format is {"character": [xxx,...]}
                if response:
                    response = response.data
                    if self.caching:
                        Cache().putIntoCache(cacheKey, str(response))
        except Exception as e:
            self.logger.error("Error retrieving Character-ID by Name \"%s\" from ESI: %r", charname, e)
            if self.caching:
                Cache().delFromCache(cacheKey)
        return response

    def getCharacterAvatar(self, characterId: int) -> Response.data:
        response = None
        try:
            if self.caching:
                cacheKey = "_".join(("esicache", "getcharavatar", str(characterId)))
                result = Cache().getFromCache(cacheKey)
                if result:
                    response = literal_eval(result)
            if not response:
                op = self.esiApp.op['get_characters_character_id_portrait'](
                    character_id=characterId)
                response = self.esiClient.request(op)
                if response:
                    response = response.data
                    if self.caching:
                        Cache().putIntoCache(cacheKey, str(response))
        except Exception as e:
            self.logger.error(
                "Error retrieving Character Avatar for ID \"%d\" from ESI: %r",characterId, e)
            if self.caching:
                Cache().delFromCache(cacheKey)
        return response

    def getCharacterAvatarByName(self, characterName: str) -> Response.data:
        resp = self.getCharacterId(characterName, True)
        if resp:
            return self.getCharacterAvatar(resp["character"][0])
        return resp

    def getSystemIds(self, namelist: list) -> Response.data:
        response = None
        try:
            if self.caching:
                cacheKey = "_".join(("esicache", "getsystemids", str(namelist)))
                result = Cache().getFromCache(cacheKey)
                if result:
                    response = literal_eval(result)
            if not response:
                op = self.esiApp.op['post_universe_ids'](names=namelist)
                response = self.esiClient.request(op)
                if response:
                    response = response.data
                    if self.caching:
                        Cache().putIntoCache(cacheKey, str(response))
                    # format is [{"name": xx, "id": xx} ...]
        except Exception as e:
            self.logger.error("Error retrieving System-IDs for \"%r\" from ESI: %r".namelist, e)
            if self.caching:
                Cache().delFromCache(cacheKey)
        return response

    def getSystemNames(self, idlist: list) -> Response.data:
        response = None
        try:
            if self.caching:
                cacheKey = "_".join(("esicache", "getsystemnames", str(idlist)))
                result = Cache().getFromCache(cacheKey)
                if result:
                    response = literal_eval(result)
            if not response:
                op = self.esiApp.op['post_universe_names'](ids=idlist)
                response = self.esiClient.request(op)
                # format is [{"category": xx, "name": xx, "id": xx} ...]
                if response:
                    response = response.data
                    if self.caching:
                        Cache().putIntoCache(cacheKey, str(response))
        except Exception as e:
            self.logger.error("Error retrieving System-Names for \"%r\" from ESI: %r", idlist, e)
            if self.caching:
                Cache().delFromCache(cacheKey)

        return response

    # not caching this
    def getKills(self) -> (Response.data, datetime.datetime):
        response = None
        expiry = None
        try:
            op = self.esiApp.op['get_universe_system_kills']()
            response = self.esiClient.request(op)
            if response:
                expiry = self.calcExpiryResponse(response)
                response = response.data
                # format is [{"npc_kills": xx, "pod_kills": xx, "ship_kills": xx, ""system_id": xx} ...]
        except Exception as e:
            self.logger.error("Error retrieving Kills from ESI", e)
        return response, expiry

    # not caching this
    def getJumps(self) -> (Response.data, datetime.datetime):
        response = None
        expiry = None
        try:
            op = self.esiApp.op['get_universe_system_jumps']()
            response = self.esiClient.request(op)
            if response:
                expiry = self.calcExpiryResponse(response)
                response = response.data
                # format is [{"ship_jumps": xx, "system_id": xx} ...]
        except Exception as e:
            self.logger.error("Error retrieving Jumps from ESI", e)
        return response, expiry

    def getShipGroups(self) -> Response.data:
        response = None
        try:
            if self.caching:
                cacheKey = "_".join(("esicache", "getshipgroups"))
                response = EsiCache().get(cacheKey)
            if not response:
                # this will return Groups of type 6 (ship)
                op = self.esiApp.op['get_universe_categories_category_id'](category_id=6)
                response = self.esiClient.request(op)
                if response:
                    response = response.data
                    if self.caching:
                        EsiCache().set(cacheKey, response)
                # format is [{"ship_jumps": xx, "system_id": xx} ...]
        except Exception as e:
            self.logger.error("Error retrieving Ship-Groups from ESI", e)
            if self.caching:
                EsiCache().invalidate(cacheKey)
        return response

    def getShipGroupTypes(self, groupid: int) -> Response.data:
        response = None
        try:
            if self.caching:
                cacheKey = "_".join(("esicache", "getshipgrouptype", str(groupid)))
                response = EsiCache().get(cacheKey)
            if not response:
                # this will return Groups of type 6 (ship)
                op = self.esiApp.op['get_universe_groups_group_id'](group_id=groupid)
                response = self.esiClient.request(op)
                if response:
                    response = response.data
                    if self.caching:
                        EsiCache().set(cacheKey, response)
                # format is [{"ship_jumps": xx, "system_id": xx} ...]
        except Exception as e:
            self.logger.error("Error retrieving Ship-Group-Types from ESI", e)
            if self.caching:
                EsiCache().invalidate(cacheKey)
        return response

    def getShip(self, shipid: int) -> Response.data:
        response = None
        try:
            if self.caching:
                cacheKey = "_".join(("esicache", "getship", str(shipid)))
                response = EsiCache().get(cacheKey)
            if not response:
                # this will return Groups of type 6 (ship)
                op = self.esiApp.op['get_universe_types_type_id'](type_id=shipid)
                response = self.esiClient.request(op)
                if response:
                    response = response.data
                    if self.caching:
                        EsiCache().set(cacheKey, response)
                    # format is [{"ship_jumps": xx, "system_id": xx} ...]
        except Exception as e:
            self.logger.error("Error retrieving Ship from ESI", e)
            if self.caching:
                EsiCache().invalidate(cacheKey)
        return response

    @property
    def getShipList(self) -> list:
        ships = []
        try:
            if self.caching:
                cacheKey = "_".join(("esicache", "getshiplist"))
                ships = EsiCache().get(cacheKey)
            if ships is None or len(ships) == 0:
                self.logger.debug("Loading Ship-Data...")
                ships = []
                shipgroup = self.getShipGroups()
                for group in shipgroup['groups']:
                    shiptypes = self.getShipGroupTypes(group)
                    for ship in shiptypes['types']:
                        shipitem = self.getShip(ship)
                        ships.append(shipitem)
                EsiCache().set(cacheKey, ships)
                self.logger.debug("Loading Ship-Data...complete")
        except Exception as e:
            self.logger.error("Error retrieving Ship-List from ESI", e)
            if self.caching:
                EsiCache().invalidate(cacheKey)

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


from PyQt5.QtCore import QThread, QTimer
import time
import queue

# This is purely to load ESI in the background, since it can take quite a while!
# Once loaded, the thread can actually be stopped
class EsiThread(QThread):
    POLL_RATE = 5000

    def __init__(self):
        QThread.__init__(self)
        self.queue = queue.Queue(maxsize=1)
        self.lastStatisticsUpdate = time.time()
        self.pollRate = self.POLL_RATE
        self.refreshTimer = None
        self.active = True

    def requestInstance(self):
        self.queue.put(1)

    def run(self):
        self.refreshTimer = QTimer()
        self.refreshTimer.timeout.connect(self.requestInstance)
        while True:
            # Block waiting for requestStatistics() to enqueue a token
            self.queue.get()
            if not self.active:
                return
            # this should stop any kind of future polling
            self.refreshTimer.stop()
            logging.debug("EsiThread creating Instance")
            # this can take a while... loading Swagger and loading Ship-Data
            try:
                # load the Interface
                EsiInterface()
                EsiInterface().getShipList
            except Exception as e:
                logging.error("Error in EsiThread: %r", e)
                exit(-1)
            self.lastStatisticsUpdate = time.time()
            self.refreshTimer.start(self.pollRate)

    def quit(self):
        self.active = False
        self.queue.put(None)
        QThread.quit(self)

