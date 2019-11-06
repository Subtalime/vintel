#   Copyright (c) 2019. Steven Tschache (github@tschache.com)
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	 See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.	 If not, see <http://www.gnu.org/licenses/>.
#

import logging
import datetime
import webbrowser
import functools
import threading
import os
from http.client import HTTPException
from pyswagger.io import Response
from esipy import EsiClient, EsiApp, EsiSecurity
from esipy.utils import generate_code_verifier
from esipy.security import APIException
from esipy.events import AFTER_TOKEN_REFRESH
from .esicache import EsiCache
from .esiconfig import EsiConfig
from .esiconfigdialog import EsiConfigDialog
from .esiwait import EsiWait

lock = threading.Lock()

logger = logging.getLogger(__name__)

def _after_token_refresh(access_token, refresh_token, expires_in, **kwargs):
    logger.info("TOKEN We got new token: %s" % access_token)
    logger.info("TOKEN refresh token used: %s" % refresh_token)
    logger.info("TOKEN Expires in %d" % expires_in)

def logrepr(className: type) -> str:
    return str(className).replace("'", "").replace("__main__.", "").replace("<", "").replace(">",
                                                                                             "")
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


class EsiInterface(metaclass=EsiInterfaceType):
    _instance = None
    secretKey = None
    _esiLoading = False

    # make it a Singleton
    class __OnceOnly:
        def __init__(self, enablecache: bool = True):
            if EsiInterface._esiLoading:
                logger.error("Esi already currently being loaded...")
                while EsiInterface.esiLoading is not "complete":
                    pass
                return
            EsiInterface._esiLoading = True
            self.caching = enablecache
            self.esicache = EsiCache(self.caching)
            self.progress = None
            self.logger = logger
            self.logger.info("Creating ESI access")
            self.authenticated = False
            self.esiConfig = EsiConfig()
            self.server = None
            self.headers = {
                'User-Agent': "{} Intel Management Tool".format(self.esiConfig.PROGNAME)}
            self.codeverifier = generate_code_verifier()
            try:
                if not self.esiConfig.ESI_CLIENT_ID or self.esiConfig.ESI_CLIENT_ID == "":
                    cacheToken = self.esicache.get("esi_clientid")
                    if cacheToken:
                        self.esiConfig.ESI_CLIENT_ID = str(cacheToken)
                    else:
                        self.esiConfig.ESI_CLIENT_ID = None
                cacheToken = self.esicache.get("esi_callback")
                if cacheToken:
                    self.esiConfig.ESI_CALLBACK = str(cacheToken)
                # this uses PKCE (pixie) authorisation with ESI
                if not self.esiConfig.ESI_CLIENT_ID:
                    # TODO: look at PyFa to see how they do it...
                    # TODO: until then, we should stop storing the SecretKey
                    with EsiConfigDialog(self.esiConfig) as inputDia:
                        res = inputDia.exec_()
                        if not res == inputDia.Accepted:
                            logger.info("User canceled Client-ID Input-Dialog")
                            exit(0)
                        self.esiConfig = inputDia.esiConfig
                    self.esicache.set("esi_callback", self.esiConfig.ESI_CALLBACK)
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
                refreshKey = None
                tokenKey = self.esicache.get("esi_token")
                if tokenKey:
                    refreshKey = tokenKey['refresh_token']
                while not self.apiInfo:
                    try:
                        if EsiConfig.ESI_SECRET_KEY:
                            self.logger.debug("Checking the Secretkey")
                            self.tokens = self.security.auth(EsiConfig.ESI_SECRET_KEY)
                            EsiConfig.ESI_SECRET_KEY = None
                            self.apiInfo = self.security.verify()
                            # store the Token
                            self.esicache.set("esi_token", self.tokens)
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
                        APIException("Problem with the API?", e)
                        self.waitForSecretKey()
                    except AttributeError as e:
                        self.logger.error("EsiAttribute Error", e)
                        APIException("Attribute problem?", e)
                        self.waitForSecretKey()
                    except Exception as e:
                        self.logger.error("Some unexpected error in Esi", e)
                        raise

                if self.logger:
                    self.logger.debug("ESI loading Swagger...")
                    # outputs a load of data in Debug
                    oldSetting = self.logger.getEffectiveLevel()
                    self.logger.setLevel(logging.WARN)
                while not self.esiApp:
                    try:
                        self.esiApp = EsiApp(cache=EsiCache(self.caching),
                                             cache_time=3 * 86400).get_latest_swagger
                    except (Exception, HTTPException) as e:
                        self.logger.error("Error while retrieving latest Swagger", e)
                        if e.code == 500:
                            self.esicache.invalidateAll()
                            self.logger.exception("ESI-Interface not explicitly instantiated!")
                            raise

                            # Reset logging to old level
                self.logger.setLevel(oldSetting)
                self.logger.debug("ESI loading Swagger...complete")
                self.logger.debug("Finished authorizing with ESI")
                self.authenticated = True
                # now we can store the Client-ID
                self.esicache.set("esi_clientid", self.esiConfig.ESI_CLIENT_ID)

            except Exception as e:
                self.logger.critical("Error authenticating with ESI", e)
                raise
            EsiInterface.esiLoading = "complete"

        def waitForSecretKey(self):
            # Take the user to the EVE-Auth page in a Browser-Window
            ssoUri = self.security.get_auth_uri(
                state="Authentication for {}".format(self.esiConfig.PROGNAME),
                scopes=None
            )
            webbrowser.open(ssoUri)
            # Wait for the user to complete login or cancel
            wait_dialog = EsiWait()
            wait_dialog.exec_()
            if not EsiConfig.ESI_SECRET_KEY:
                # User decided to cancel the operation

                exit(0)

        def __str__(self):
            return repr(self)

    def __init__(self, use_caching: bool = True, cache_dir: str = None):
        if not EsiInterface._instance:
            self.caching = use_caching
            self.logger = logger
            if self.caching and cache_dir:
                EsiCache.BASE_DIR = cache_dir
            AFTER_TOKEN_REFRESH.add_receiver(_after_token_refresh)
            try:
                EsiInterface._instance = EsiInterface.__OnceOnly(enablecache=self.caching)
            except Exception as e:
                exit(-1)
        self.cache = EsiCache(self.caching)

    def __getattr__(self, name):
        return getattr(self._instance, name)

    def calcExpiry(self, expireDate: str) -> datetime.datetime:
        cache_until = datetime.datetime.strptime(expireDate, "%a, %d %b %Y %H:%M:%S %Z")
        diff = cache_until - self.currentEveTime()
        return diff

    def calcExpiryResponse(self, resp: Response) -> datetime.datetime:
        return self.calcExpiry(resp.header.get('Expires')[0])

    @staticmethod
    def _copyModel(data) -> dict:
        retval = {}
        for key, val in data.items():
            retval[key] = val
        return retval

    def getCharacter(self, characterId: int) -> Response.data:
        # Character-Caching is based on EveTime... we want to reload after Eve is back up
        cacheKey = "_".join(("esicache", "getcharacter", str(characterId)))
        response = self.cache.getFromCache(cacheKey)
        if not response:
            try:
                op = self.esiApp.op['get_characters_character_id'](character_id=characterId)
                response = self.esiClient.request(op)
                # format is {"alliance_id": xx, "ancestry_id": xx, "birthday": xx, "bloodline_id": xx,
                # "corporation_id": xx, "description": xx, "gender": xx, "name": xx, "race_id": xx,
                # "security_status": xx, "title": xx}
                if response:
                    expiry = self.calcExpiry(response.header.get('Expires')[0])
                    response = self._copyModel(response.data)
                    self.cache.putIntoCache(cacheKey, response, expiry.seconds)
            except Exception as e:
                self.cache.delFromCache(cacheKey)
                self.logger.error("Error retrieving Character \"%d\" from ESI: %r", characterId, e)
                raise
        return response

    def getCorporation(self, corpid: int) -> Response.data:
        try:
            cacheKey = "_".join(("esicache", "getcorporation", str(corpid)))
            response = self.cache.getFromCache(cacheKey)
            if not response:
                op = self.esiApp.op['get_corporations_corporation_id'](corporation_id=corpid)
                response = self.esiClient.request(op)
                if response:
                    response = response.data
                    self.cache.putIntoCache(cacheKey, response)
                # format is {"alliance_id": xx, "ceo_id": xx, "creator_id": xx, "data_founded": xx,
                #           "description": xx, "war_elligible": xx, "url": xx, "ticker": xx,
                #           "shares": xx, "name": xx, "member_count": xx,
                #            "home_station_id": xx }
        except Exception as e:
            self.cache.delFromCache(cacheKey)
            self.logger.error("Error retrieving Corporation \"%d\" from ESI: %r", corpid, e)
            raise
        return response

    def getCorporationHistory(self, characterId: int) -> Response.data:
        response = None
        try:
            # this wont store and retrieve correctly, but nevermind
            cacheKey = "_".join(("esicache", "getcorporationhist", str(characterId)))
            response = self.cache.getFromCache(cacheKey)
            if not response:
                op = self.esiApp.op['get_characters_character_id_corporationhistory'](
                    character_id=characterId)
                response = self.esiClient.request(op)
                if response:
                    response = response.data
                    self.cache.putIntoCache(cacheKey, response)
                    # format is {"corporation_id": xx, "record_id": xx, "start_date": xx},...
        except Exception as e:
            self.cache.delFromCache(cacheKey)
            self.logger.error(
                    "Error retrieving Corporation-History for Character \"%d\" from ESI: %r",
                    characterId, e)
            raise
        return response

    def getCharacterId(self, charname: str, strict: bool = True) -> Response.data:
        response = None
        try:
            cacheKey = "_".join(
                ("esicache", "getcharacterid", "0" if not strict else "1", charname))
            response = self.cache.getFromCache(cacheKey)
            if not response:
                op = self.esiApp.op['get_search'](categories='character', search=charname,
                                                  strict=strict)
                response = self.esiClient.request(op)
                # format is {"character": [xxx,...]}
                if response:
                    response = response.data
                    self.cache.putIntoCache(cacheKey, response)
        except Exception as e:
            self.cache.delFromCache(cacheKey)
            self.logger.error("Error retrieving Character-ID by Name \"%s\" from ESI: %r",
                                  charname, e)
            raise
        return response

    def getCharacterAvatar(self, characterId: int) -> Response.data:
        response = None
        try:
            cacheKey = "_".join(("esicache", "getcharavatar", str(characterId)))
            response = self.cache.getFromCache(cacheKey)
            if not response:
                op = self.esiApp.op['get_characters_character_id_portrait'](
                    character_id=characterId)
                response = self.esiClient.request(op)
                if response:
                    response = response.data
                    self.cache.putIntoCache(cacheKey, response)
        except Exception as e:
            self.cache.delFromCache(cacheKey)
            self.logger.error(
                    "Error retrieving Character Avatar for ID \"%d\" from ESI: %r", characterId, e)
            raise
        return response

    def getCharacterAvatarByName(self, characterName: str) -> Response.data:
        resp = self.getCharacterId(characterName, True)
        if resp:
            return self.getCharacterAvatar(resp["character"][0])
        return resp

    def getSystemIds(self, namelist: list) -> Response.data:
        response = None
        try:
            cacheKey = "_".join(("esicache", "getsystemids", str(namelist)))
            response = self.cache.getFromCache(cacheKey)
            if not response:
                op = self.esiApp.op['post_universe_ids'](names=namelist)
                response = self.esiClient.request(op)
                if response:
                    response = response.data
                    self.cache.putIntoCache(cacheKey, response)
                    # format is [{"name": xx, "id": xx} ...]
        except Exception as e:
            self.cache.delFromCache(cacheKey)
            self.logger.error("Error retrieving System-IDs for \"%r\" from ESI: %r", namelist,
                                  e)
            raise
        return response

    def getSystemNames(self, idlist: list) -> Response.data:
        response = None
        try:
            cacheKey = "_".join(("esicache", "getsystemnames", str(idlist)))
            response = self.cache.getFromCache(cacheKey)
            if not response:
                op = self.esiApp.op['post_universe_names'](ids=idlist)
                response = self.esiClient.request(op)
                # format is [{"category": xx, "name": xx, "id": xx} ...]
                if response:
                    response = response.data
                    self.cache.putIntoCache(cacheKey, response)
        except Exception as e:
            self.cache.delFromCache(cacheKey)
            self.logger.error("Error retrieving System-Names for \"%r\" from ESI: %r", idlist, e)
            raise
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
            raise
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
            raise
        return response, expiry

    def getShipGroups(self) -> Response.data:
        response = None
        try:
            cacheKey = "_".join(("esicache", "getshipgroups"))
            response = self.cache.get(cacheKey)
            if not response:
                # this will return Groups of type 6 (ship)
                op = self.esiApp.op['get_universe_categories_category_id'](category_id=6)
                response = self.esiClient.request(op)
                if response:
                    response = response.data
                    self.cache.set(cacheKey, response)
                # format is [{"ship_jumps": xx, "system_id": xx} ...]
        except Exception as e:
            self.cache.delFromCache(cacheKey)
            self.logger.error("Error retrieving Ship-Groups from ESI", e)
            raise
        return response

    def getShipGroupTypes(self, groupid: int) -> Response.data:
        response = None
        try:
            cacheKey = "_".join(("esicache", "getshipgrouptype", str(groupid)))
            response = self.cache.get(cacheKey)
            if not response:
                # this will return Groups of type 6 (ship)
                op = self.esiApp.op['get_universe_groups_group_id'](group_id=groupid)
                response = self.esiClient.request(op)
                if response:
                    response = response.data
                    self.cache.set(cacheKey, response)
                # format is [{"ship_jumps": xx, "system_id": xx} ...]
        except Exception as e:
            self.cache.delFromCache(cacheKey)
            self.logger.error("Error retrieving Ship-Group-Types from ESI", e)
            raise
        return response

    def getShip(self, shipid: int) -> Response.data:
        response = None
        try:
            cacheKey = "_".join(("esicache", "getship", str(shipid)))
            response = self.cache.get(cacheKey)
            if not response:
                # this will return Groups of type 6 (ship)
                op = self.esiApp.op['get_universe_types_type_id'](type_id=shipid)
                response = self.esiClient.request(op)
                if response:
                    response = response.data
                    self.cache.set(cacheKey, response)
                    # format is [{"ship_jumps": xx, "system_id": xx} ...]
        except Exception as e:
            self.cache.delFromCache(cacheKey)
            self.logger.error("Error retrieving Ship from ESI", e)
            raise
        return response

    @property
    def getShipList(self) -> list:
        ships = []
        try:
            cacheKey = "_".join(("esicache", "getshiplist"))
            ships = self.cache.get(cacheKey)
            if ships is None or len(ships) == 0:
                if self.logger:
                    self.logger.debug("Loading Ship-Data...")
                ships = []
                shipgroup = self.getShipGroups()
                for group in shipgroup['groups']:
                    shiptypes = self.getShipGroupTypes(group)
                    for ship in shiptypes['types']:
                        shipitem = self.getShip(ship)
                        ships.append(shipitem)
                self.cache.set(cacheKey, ships)
                if self.logger:
                    self.logger.debug("Loading Ship-Data...complete")
        except Exception as e:
            self.cache.invalidate(cacheKey)
            self.logger.error("Error retrieving Ship-List from ESI", e)
            raise
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
