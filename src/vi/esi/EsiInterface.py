import logging
from esipy.utils import generate_code_verifier
from esipy import EsiClient, EsiApp, EsiSecurity
from esipy.security import APIException
from esipy.cache import BaseCache
from esipy.events import AFTER_TOKEN_REFRESH
from esiconfig import EsiConfig
from pyswagger.io import Response, CaseInsensitiveDict
import datetime
import json
import ast
from urllib.parse import urlparse, parse_qs
import vi.version
import webbrowser, threading, functools
import threading, hashlib
from vi.cache.cache import Cache
from http.server import HTTPServer, BaseHTTPRequestHandler

try:
    import pickle
except ImportError:  # pragma: no cover
    import cPickle as pickle

secretKey = None
esiLoading = False

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


def _hash(data):
    """ generate a hash from data object to be used as cache key """
    hash_algo = hashlib.new('md5')
    hash_algo.update(pickle.dumps(data))
    # prefix allows possibility of multiple applications
    # sharing same keyspace
    return 'esi_' + hash_algo.hexdigest()


class EsiCache(BaseCache):
    def __init__(self):
        self.cache = Cache("esi_cache.sqlite3", forceVersionCheck=True)

    def get(self, key, default=None):
        value = self.cache.getFromCache(_hash(key))
        return pickle.loads(value) if value is not None else default

    def set(self, key, value):
        self.cache.putIntoCache(_hash(key), pickle.dumps(value))

    def invalidate(self, key):
        self.cache.delFromCache(_hash(key))


class EsiInterface(metaclass=EsiInterfaceType):
    _instance = None

    # make it a Singleton
    class __OnceOnly:
        def __init__(self, enablecache: bool = True):
            global secretKey
            global esiLoading
            if esiLoading:
                while esiLoading is not "complete":
                    logging.error("Esi already currently being loaded...")
                    pass
                return
            esiLoading = True
            self.logger = logging.getLogger(logrepr(__class__))
            self.caching = enablecache
            self.logger.debug("Creating ESI access")
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
                if self.caching:
                    cacheToken = Cache().getFromCache("esi_token")
                    if cacheToken:
                        tokenKey = pickle.loads(cacheToken)
                while not self.apiInfo:
                    try:
                        if secretKey:
                            self.esiConfig.setSecretKey(secretKey)
                            secretKey = None
                            self.tokens = self.security.auth(self.esiConfig.getSecretKey())
                            self.apiInfo = self.security.verify()
                            # store the Token
                            if self.caching:
                                Cache().putIntoCache("esi_token", pickle.dumps(self.tokens))
                        elif tokenKey:
                            self.security.update_token(tokenKey)
                            self.apiInfo = self.security.refresh()
                        else:
                            self.waitForSecretKey()
                    except APIException as e:
                        self.logger.error("EsiAPI Error", e)
                        self.waitForSecretKey()
                    except AttributeError as e:
                        self.logger.error("EsiAttribute Error", e)
                        self.waitForSecretKey()
                    except Exception as e:
                        self.logger.error("Some unexpected error in Esi", e)

                self.logger.debug("ESI loading Swagger...")
                # outputs a load of data in Debug
                oldSetting = logging.getLogger().getEffectiveLevel()
                logging.getLogger().setLevel(logging.WARN)
                self.esiApp = EsiApp(cache=EsiCache(), cache_time=3 * 86400).get_latest_swagger
                # Reset logging to old level
                logging.getLogger().setLevel(oldSetting)
                self.logger.debug("ESI loading Swagger...complete")
                self.authenticated = True
                self.logger.debug("Finished authorizing with ESI")
            except Exception as e:
                self.logger.critical("Error authenticating with ESI", e)
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
                            global secretKey
                            secretKey = thisquery['code'][0]
                            self.wfile.write(
                                b"You have verified your account on ESI. You can now close this window")
                    except Exception as e:
                        self.logger.error("Unexpected response: {}".format(self.requestline))
                        self.wfile.write(b"I don't know what you are on about")

        def __str__(self):
            return repr(self)

    def __init__(self, useCaching: bool = True):
        if not EsiInterface._instance:
            self.caching = useCaching
            self.logger = logging.getLogger(logrepr(__class__))
            AFTER_TOKEN_REFRESH.add_receiver(_after_token_refresh)
            EsiInterface._instance = EsiInterface.__OnceOnly(useCaching)

    def __getattr__(self, name):
        return getattr(self._instance, name)

    # def _cacheVar(self, function: str, **kwargs):
    #     return "_".join(("esicache", function, for var in kwargs))
    #
    def getCharacter(self, characterId: int) -> Response:
        # Character-Caching is based on EveTime... we want to reload after Eve is back up
        response = None
        try:
            if self.caching:
                cacheKey = "_".join(("esicache", "getcharacter", str(characterId)))
                result = Cache().getFromCache(cacheKey)
                if result:
                    response = pickle.loads(result)
            if not response:
                op = self.esiApp.op['get_characters_character_id'](character_id=characterId)
                response = self.esiClient.request(op)
                # format is {"alliance_id": xx, "ancestry_id": xx, "birthday": xx, "bloodline_id": xx, "corporation_id": xx,
                #            "description": xx, "gender": xx, "name": xx, "race_id": xx, "security_status": xx, "title": xx}
                if response and self.caching:
                    expire_date = response.header.get('Expires')[0]
                    cacheUntil = datetime.datetime.strptime(expire_date, "%a, %d %b %Y %H:%M:%S %Z")
                    diff = cacheUntil - self.currentEveTime()
                    Cache().putIntoCache(cacheKey, pickle.dumps(response), diff.seconds)
        except Exception as e:
            if self.caching:
                Cache().delFromCache(cacheKey)
            self.logger.error("Error retrieving Character \"{}\" from ESI".format(characterId), e)
        return response

    def getCorporation(self, corpid: int) -> Response:
        response = None
        try:
            if self.caching:
                cacheKey = "_".join(("esicache", "getcorporation", str(corpid)))
                result = Cache().getFromCache(cacheKey)
                if result:
                    response = pickle.loads(result)
            if not response:
                op = self.esiApp.op['get_corporations_corporation_id'](corporation_id=corpid)
                response = self.esiClient.request(op)
                if response and self.caching:
                    Cache().putIntoCache(cacheKey, pickle.dumps(response))
                # format is {"alliance_id": xx, "ceo_id": xx, "creator_id": xx, "data_founded": xx, "description": xx,
                #            "war_elligible": xx, "url": xx, "ticker": xx, "shares": xx, "name": xx, "member_count": xx,
                #            "home_station_id": xx }
        except Exception as e:
            self.logger.error("Error retrieving Corporation \"{}\" from ESI".format(corpid), e)
            if self.caching:
                Cache().delFromCache(cacheKey)
        return response

    def getCorporationHistory(self, characterId: int) -> Response:
        response = None
        try:
            if self.caching:
                cacheKey = "_".join(("esicache", "getcorporationhist", str(characterId)))
                result = Cache().getFromCache(cacheKey)
                if result:
                    response = pickle.loads(result)
            if not response:
                op = self.esiApp.op['get_characters_character_id_corporationhistory'](
                    character_id=characterId)
                response = self.esiClient.request(op)
                if response and self.caching:
                    Cache().putIntoCache(cacheKey, pickle.dumps(response))
                # format is {"corporation_id": xx, "record_id": xx, "start_date": xx},...
        except Exception as e:
            self.logger.error(
                "Error retrieving Corporation-History for Character \"{}\" from ESI".format(
                    characterId), e)
            if self.caching:
                Cache().delFromCache(cacheKey)
        return response

    def getCharacterId(self, charname: str, strict: bool = True) -> Response:
        response = None
        try:
            cacheKey = "_".join(("esicache", "getcharacterid", charname))
            if self.caching:
                result = Cache().getFromCache(cacheKey)
                if result:
                    response = pickle.loads(result)
            if not response:
                op = self.esiApp.op['get_search'](categories='character', search=charname,
                                                  strict=strict)
                response = self.esiClient.request(op)
                # format is {"character": [xxx,...]}
                if response and self.caching:
                    Cache().putIntoCache(cacheKey, pickle.dumps(response))
        except Exception as e:
            self.logger.error("Error retrieving Character-ID by Name \"{}\" from ESI".format(charname),
                              e)
            if self.caching:
                Cache().delFromCache(cacheKey)
        return response

    def getCharacterAvatar(self, characterId: int) -> Response:
        response = None
        try:
            if self.caching:
                cacheKey = "_".join(("esicache", "getcharavatar", str(characterId)))
                result = Cache().getFromCache(cacheKey)
                if result:
                    response = pickle.loads(result)
            if not response:
                op = self.esiApp.op['get_characters_character_id_portrait'](
                    character_id=characterId)
                response = self.esiClient.request(op)
                if response and self.caching:
                    Cache().putIntoCache(cacheKey, pickle.dumps(response))
        except Exception as e:
            self.logger.error(
                "Error retrieving Character Avatar for ID \"{}\" from ESI".format(characterId), e)
            if self.caching:
                Cache().delFromCache(cacheKey)
        return response

    def getCharacterAvatarByName(self, characterName: str) -> Response:
        resp = self.getCharacterId(characterName, True)
        if resp:
            return self.getCharacterAvatar(resp.data["character"][0])
        return resp

    def getSystemIds(self, namelist: list) -> Response:
        response = None
        try:
            if self.caching:
                cacheKey = "_".join(("esicache", "getsystemids", str(namelist)))
                result = Cache().getFromCache(cacheKey)
                if result:
                    response = pickle.loads(result)
            if not response:
                op = self.esiApp.op['post_universe_ids'](names=namelist)
                response = self.esiClient.request(op)
                if response and self.caching:
                    Cache().putIntoCache(cacheKey, pickle.dumps(response))
                # format is [{"name": xx, "id": xx} ...]
        except Exception as e:
            self.logger.error("Error retrieving System-IDs for \"{}\" from ESI".format(namelist), e)
            if self.caching:
                Cache().delFromCache(cacheKey)
        return response

    def getSystemNames(self, idlist: list) -> Response:
        response = None
        try:
            if self.caching:
                cacheKey = "_".join(("esicache", "getsystemnames", str(idlist)))
                result = Cache().getFromCache(cacheKey)
                if result:
                    response = pickle.loads(result)
            if not response:
                op = self.esiApp.op['post_universe_names'](ids=idlist)
                response = self.esiClient.request(op)
                # format is [{"category": xx, "name": xx, "id": xx} ...]
                if response and self.caching:
                    Cache().putIntoCache(cacheKey, pickle.dumps(response))
        except Exception as e:
            self.logger.error("Error retrieving System-Names for \"{}\" from ESI".format(idlist), e)
            if self.caching:
                Cache().delFromCache(cacheKey)

        return response

    # not caching this
    def getKills(self) -> Response:
        response = None
        try:
            op = self.esiApp.op['get_universe_system_kills']()
            response = self.esiClient.request(op)
            # format is [{"npc_kills": xx, "pod_kills": xx, "ship_kills": xx, ""system_id": xx} ...]
        except Exception as e:
            self.logger.error("Error retrieving Kills from ESI", e)
        return response

    # not caching this
    def getJumps(self) -> Response:
        response = None
        try:
            op = self.esiApp.op['get_universe_system_jumps']()
            response = self.esiClient.request(op)
            # format is [{"ship_jumps": xx, "system_id": xx} ...]
        except Exception as e:
            self.logger.error("Error retrieving Jumps from ESI", e)
        return response

    def getShipGroups(self) -> Response.data:
        response = None
        try:
            if self.caching:
                cacheKey = "_".join(("esicache", "getshipgroups"))
                result = Cache().getFromCache(cacheKey)
                if result:
                    response = pickle.loads(result)
            if not response:
                # this will return Groups of type 6 (ship)
                op = self.esiApp.op['get_universe_categories_category_id'](category_id=6)
                response = self.esiClient.request(op)
                if response and self.caching:
                    data = response.to_dict()
                    data = pickle.dumps(response)
                    Cache().putIntoCache(cacheKey, data)
                # format is [{"ship_jumps": xx, "system_id": xx} ...]
                response = response.data
        except Exception as e:
            self.logger.error("Error retrieving Ship-Groups from ESI", e)
            if self.caching:
                Cache().delFromCache(cacheKey)
        return response

    def getShipGroupTypes(self, groupid: int) -> Response.data:
        response = None
        try:
            if self.caching:
                cacheKey = "_".join(("esicache", "getshipgrouptype", str(groupid)))
                result = Cache().getFromCache(cacheKey)
                if result:
                    response = pickle.loads(result)
            if not response:
                # this will return Groups of type 6 (ship)
                op = self.esiApp.op['get_universe_groups_group_id'](group_id=groupid)
                response = self.esiClient.request(op)
                if response and self.caching:
                    Cache().putIntoCache(cacheKey, pickle.dumps(response.data))
                # format is [{"ship_jumps": xx, "system_id": xx} ...]
                response = response.data
        except Exception as e:
            self.logger.error("Error retrieving Ship-Group-Types from ESI", e)
            if self.caching:
                Cache().delFromCache(cacheKey)
        return response

    def getShip(self, shipid: int) -> Response.data:
        response = None
        try:
            if self.caching:
                cacheKey = "_".join(("esicache", "getship", str(shipid)))
                result = Cache().getFromCache(cacheKey)
                if result:
                    response = pickle.loads(result)
            if not response:
                # this will return Groups of type 6 (ship)
                op = self.esiApp.op['get_universe_types_type_id'](type_id=shipid)
                response = self.esiClient.request(op)
                if response and self.caching:
                    Cache().putIntoCache(cacheKey, pickle.dumps(response.data))
                # format is [{"ship_jumps": xx, "system_id": xx} ...]
                response = response.data
        except Exception as e:
            self.logger.error("Error retrieving Ship from ESI", e)
            if self.caching:
                Cache().delFromCache(cacheKey)
        return response

    @property
    def getShipList(self):
        ships = []
        try:
            if self.caching:
                cacheKey = "_".join(("esicache", "getshiplist"))
                result = Cache().getFromCache(cacheKey)
                if result:
                    ships = pickle.loads(result)
            if len(ships) == 0:
                shipgroup = self.getShipGroups()
                for group in shipgroup['groups']:
                    shiptypes = self.getShipGroupTypes(group)
                    for ship in shiptypes['types']:
                        shipitem = self.getShip(ship)
                        ships.append(shipitem)
                Cache().putIntoCache(cacheKey, pickle.dumps(ships), 30 * 24 * 60 * 60)
        except Exception as e:
            self.logger.error("Error retrieving Ship-List from ESI", e)
            if self.caching:
                Cache().delFromCache(cacheKey)

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
            self.refreshTimer.stop()
            logging.debug("EsiThread creating Instance")
            try:
                EsiInterface()
                EsiInterface().getShipList

            except Exception as e:
                logging.error("Error in EsThread: %s", e)
            self.lastStatisticsUpdate = time.time()
            self.refreshTimer.start(self.pollRate)

    def quit(self):
        self.active = False
        self.queue.put(None)
        QThread.quit(self)


if __name__ == "__main__":
    def _cacheVar(function: str, *argv):
        args = argv.__repr__()
        l = []
        for a in argv:
            l.append(str(a))
        return "_".join(("esicache", function)) + "_".join((str(argv.__repr__())))


    a = _cacheVar("test", 1, "me")

    import requests, datetime

    log_format = '%(asctime)s %(levelname)-8s: %(name)s/%(funcName)s %(message)s'
    log_format_con = '%(levelname)-8s: %(name)s/%(funcName)s %(message)s'
    log_date = '%m/%d/%Y %I:%M:%S %p'
    log_date = '%H:%M:%S'
    logging.basicConfig(level=logging.DEBUG,
                        format=log_format,
                        datefmt=log_date)
    # console = logging.StreamHandler()
    # console.setLevel(level=logging.DEBUG)
    # console.setFormatter(logging.Formatter(log_format_con))
    #
    # logger = logging.getLogger(__name__)
    # logger.addHandler(console)
    # logging.getLogger().setLevel(logging.DEBUG)

    thread = EsiThread()
    thread.start(1)
    thread.requestInstance()
    time.sleep(2)
    esi = EsiInterface()
    thread.quit()
    es2 = EsiInterface()
    ships = esi.getShipList

    shipgroup = esi.getShipGroups()
    for group in shipgroup['groups']:
        shiptypes = esi.getShipGroupTypes(group)
        for ship in shiptypes['types']:
            shipitem = esi.getShip(ship)
            ships.append(shipitem)

    res = esi.getSystemNames([95465449, 30000142])

    chari = esi.getCharacterId("Tablot Manzari")
    if chari:
        print("getCharacterId: {}".format(chari.data))
        charid = chari.data['character'][0]
        chara = esi.getCharacter(charid)

        character = chara.data  # Tablot Manzari
        expire_date = chara.header.get('Expires')[0]
        cacheUntil = datetime.datetime.strptime(expire_date, "%a, %d %b %Y %H:%M:%S %Z")
        print("getCharacter: {} expires {}".format(character, cacheUntil))

        avatars = esi.getCharacterAvatar(charid)  # Tablot Manzari
        print("getCharacterAvatar: {}".format(avatars.data))
        imageurl = avatars.data["px64x64"]
        avatar = requests.get(imageurl).content
        corphist = esi.getCorporationHistory(charid)  # Bovril
        print("getCorporationHistory: {}".format(corphist.data))
        corp = esi.getCorporation(character['corporation_id'])  # Bovril
        print("getCorporation: {}".format(corp.data))
    li = ["B-7DFU", "Jita"]
    ids = esi.getSystemIds(li)
    if ids:
        print("getSystemIds: {}".format(ids.data))
        li = []
        sys = ids.data['systems']
        for a in sys:
            li.append(a['id'])
        names = esi.getSystemNames(li)
        if names:
            print("getSystemNames: {}".format(names.data))
    jump_result = EsiInterface().getJumps()
    if jump_result:
        print("getJumps :{}".format(jump_result.data))
        jumpData = {}
        for data in jump_result.data:
            jumpData[int(data['system_id'])] = int(data['ship_jumps'])
    kill_result = EsiInterface().getKills()
    if kill_result:
        print("getKils :{}".format(kill_result.data))
