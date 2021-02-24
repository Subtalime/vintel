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
import functools
import threading
from http.client import HTTPException
from pyswagger.io import Response
from esipy import EsiClient, EsiApp
from esipy.events import AFTER_TOKEN_REFRESH
from vi.esi.esicache import EsiCache
from vi.esi.esiconfig import EsiConfig

lock = threading.Lock()


def _after_token_refresh(access_token, refresh_token, expires_in, **kwargs):
    logging.getLogger().info("TOKEN We got new token: %s" % access_token)
    logging.getLogger().info("TOKEN refresh token used: %s" % refresh_token)
    logging.getLogger().info("TOKEN Expires in %d" % expires_in)


def logrepr(className: type) -> str:
    return (
        str(className)
        .replace("'", "")
        .replace("__main__.", "")
        .replace("<", "")
        .replace(">", "")
    )


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
    security = None
    ESI_DEFAULT_TIMEOUT = 10000  # 10 seconds
    ESI_MAX_DURATION = 1500      # 1.5 second

    # make it a Singleton
    class __OnceOnly:
        def __init__(self, enable_cache: bool = True, ignore_security: bool = True):
            if EsiInterface._esiLoading:
                logging.getLogger(__name__).error(
                    "Esi already currently being loaded..."
                )
                while EsiInterface.esiLoading != "complete":
                    pass
                return
            EsiInterface._esiLoading = True
            self.LOGGER = logging.getLogger(__name__)
            self.caching = enable_cache
            self.esicache = EsiCache(self.caching)
            self.progress = None
            # self.security = None
            self.esiClient = None
            self.LOGGER.info("Creating ESI access")
            self.authenticated = False
            self.esiConfig = EsiConfig(self.esicache)
            self.server = None
            self.esiApp = None
            self.ignoreSecurity = ignore_security
            headers = {
                "User-Agent": "{} Intel Management Tool".format(
                    self.esiConfig.PROGNAME
                ),
            }

            self.esiClient = EsiClient(retry_requests=True, headers=headers)
            self.LOGGER.debug("ESI loading Swagger...")
            # outputs a load of data in Debug
            oldSetting = self.LOGGER.getEffectiveLevel()
            self.LOGGER.setLevel(logging.WARN)
            while not self.esiApp:
                try:
                    self.esiApp = EsiApp(
                        cache=self.esicache, cache_time=3 * 86400
                    ).get_latest_swagger
                except (Exception, HTTPException) as e:
                    self.LOGGER.error("Error while retrieving latest Swagger", e)
                    if e.code == 500:
                        self.esicache.invalidateAll()
                        self.LOGGER.exception(
                            "ESI-Interface not explicitly instantiated!"
                        )
                        raise

            # Reset logging to old level
            self.LOGGER.setLevel(oldSetting)
            self.LOGGER.debug("ESI loading Swagger...complete")
            self.LOGGER.debug("Finished authorizing with ESI")
            self.authenticated = True

        def __str__(self):
            return repr(self)

    def __init__(self, use_caching: bool = True, cache_dir: str = None, ignore_security: bool = True):
        self.LOGGER = logging.getLogger(__name__)
        if not EsiInterface._instance:
            self.caching = use_caching
            if self.caching and cache_dir:
                EsiCache.BASE_DIR = cache_dir
            AFTER_TOKEN_REFRESH.add_receiver(_after_token_refresh)
            try:
                EsiInterface._instance = EsiInterface.__OnceOnly(
                    enable_cache=self.caching,
                    ignore_security=ignore_security,
                )
            except Exception:
                sys.exit(-1)
        self.cache = EsiCache(self.caching)
        # disable info-logging in PySwagger
        logging.getLogger("pyswagger.core").setLevel(logging.WARNING)
        # start off with disabling ESI for 10 seconds
        self.esi_timeout = self.ESI_DEFAULT_TIMEOUT  # 10 seconds
        # Calls to ESI shouldn't take longer than 1 second
        self.esi_max_call_duration = self.ESI_MAX_DURATION

    def __getattr__(self, name):
        return getattr(self._instance, name)

    def calcExpiry(self, expireDate: str) -> int:
        """
        convert the Expiry String and deduct the Eve-Uptime to figure out the
        remaining time in seconds
        :param expireDate: datetime string
        :return: seconds: int
        """
        cache_until = datetime.datetime.strptime(expireDate, "%a, %d %b %Y %H:%M:%S %Z")
        diff = (cache_until - self.currentEveTime()).total_seconds()
        return int(diff)

    def calcExpiryResponse(self, resp: Response) -> int:
        """
        get the Expiry time we received from ESI
        :param resp: Response
        :return: seconds: int
        """
        return self.calcExpiry(resp.header.get("Expires")[0])

    @staticmethod
    def _copyModel(data) -> dict:
        """
        some items in ESI don't have a "__getattr__", so pickle wont work
        here we make a new dictionary, which copies the __repr__ value, which is storable
        :param data: Response.data
        :return: dict
        """
        retval = {}
        # if it's not a Dictionary, we don't have to worry
        if not isinstance(data, dict):
            return data
        # get the __repr__ values
        for key, val in data.items():
            retval[key] = val
        return retval

    def _allowCallToEsi(self, call_start=None, force_disable: bool = False) -> bool:
        """
        if previous attempts took longer than expected, reduce the number of calls to ESI until
        the connections speed improves... do this incrementally
        :return: if call to ESI is permitted at this time
        :type bool
        """
        now = datetime.datetime.now()
        if force_disable:
            self.cache.put("esi_allowed", False, self.esi_timeout)
            self.cache.put("esi_last_try", now, self.esi_timeout)
            return not force_disable
        if not call_start:
            esi_allowed = self.cache.fetch("esi_allowed", outdated=False, default=True)
            if not esi_allowed:
                last_try = self.cache.fetch("esi_last_try", outdated=False, default=None)
                if last_try:
                    if (now - last_try).total_seconds() * 1000 > self.esi_timeout:
                        self.esi_timeout += self.esi_timeout
                        self.cache.put("esi_last_try", now, self.esi_timeout)
                        self.cache.put("esi_allowed", True, self.esi_timeout)
                        self.LOGGER.info(
                            "Call to ESI Re-Enabled. Next delay will be %ds",
                            self.esi_timeout / 1000,
                        )
                        return True
            return esi_allowed
        call_duration = (now - call_start).total_seconds() * 1000
        if call_duration > self.esi_max_call_duration:
            self.LOGGER.info(
                "Call to ESI took %ds. Too long, so disabling ESI", call_duration / 1000
            )
            return self._allowCallToEsi(force_disable=True)
        return True

    def __del__(self):
        # prevent an increase of the timeout once program restarts
        self.cache.delete(["esi_last_try", "esi_allowed"])

    def _getResponse(self, operation, cache_expiry_secs, **kwargs):
        """
        Do a Swagger-Call to ESI-Api if we can't find the information in Cache
        if we found some data, store it in Cache for a given expiry, or until downtime
        :param operation: str
        :param cache_expiry_secs: int
        :param kwargs: dict
        :return: Response
        """
        cache_key = "_".join(("esicache", operation))
        for key in kwargs.keys():
            cache_key = "_".join((cache_key, str(kwargs[key])))
        # check if we have it in Cache
        response = self.cache.fetch(cache_key)
        if not response:
            try:
                # call the Swagger interface
                operation_call = self.esiApp.op[operation](**kwargs)
                if not self._allowCallToEsi():
                    return None
                start_call = datetime.datetime.now()
                response = self.esiClient.request(operation_call)
                self._allowCallToEsi(start_call)
                if response:
                    # use default expiry handed back by ESI
                    if not cache_expiry_secs:
                        try:
                            cache_expiry_secs = self.calcExpiryResponse(response)
                        except Exception:
                            pass
                    # some items in the response may not be storable... so make a storable copy
                    response = self._copyModel(response.data)
                    # save data in Cache
                    self.cache.put(cache_key, response, cache_expiry_secs)
            except Exception as e:
                self.cache.delete(cache_key)
                self.LOGGER.error(
                    "Error executing Operation [%s] %r" % (operation, kwargs), e
                )
                raise
        return response

    def getCharacter(self, characterId: int) -> Response.data:
        """
        for a give Character-ID return all public details
        :param characterId: int
        :return: Response.data
                 format is {"alliance_id": xx, "ancestry_id": xx, "birthday": xx, "bloodline_id": xx, "corporation_id": xx,
                            "description": xx, "gender": xx, "name": xx, "race_id": xx, "security_status": xx, "title": xx}
        """
        return self._getResponse(
            "get_characters_character_id", None, character_id=characterId
        )

    def getCorporation(self, corpid: int) -> Response.data:
        """
        for a given Corporation-ID return the details
        :param corpid: int
        :return: Response.data
                 format is {"alliance_id": xx, "ceo_id": xx, "creator_id": xx, "data_founded": xx, "description": xx,
                            "war_elligible": xx, "url": xx, "ticker": xx, "shares": xx, "name": xx, "member_count": xx,
                            "home_station_id": xx }
        """
        return self._getResponse(
            "get_corporations_corporation_id", None, corporation_id=corpid
        )

    def getCorporationHistory(self, characterId: int) -> Response.data:
        """
        for a given Character-ID return his Corporation-History
        :param characterId: int
        :return: Response.data
                 # format is {"corporation_id": xx, "record_id": xx, "start_date": xx},...
        """
        return self._getResponse(
            "get_characters_character_id_corporationhistory",
            None,
            character_id=characterId,
        )

    def getCharacterId(self, charname: str, strict: bool = True) -> Response.data:
        """
        for a given Character-Name return a list of matching Characters.
        if "strict", then don't do a "close match"
        :param charname: str
        :param strict: bool
        :return: Response.data
                 format is {"character": [xxx,...]}
        """
        return self._getResponse(
            "get_search", None, categories="character", search=charname, strict=strict
        )

    def getCharacterAvatar(self, characterId: int) -> Response.data:
        """
        for a given Character-ID return the Avatar-List
        :param characterId: int
        :return: Response.data
        """
        return self._getResponse(
            "get_characters_character_id_portrait", None, character_id=characterId
        )

    def getCharacterAvatarByName(self, characterName: str) -> Response.data:
        """
        for a given Character-Name return the Avatar-List
        :param characterName: str
        :return: Response.data
                 format is [{"name": xx, "id": xx} ...]
        """
        resp = self.getCharacterId(characterName, True)
        if resp:
            return self.getCharacterAvatar(resp["character"][0])
        return resp

    def getSystemIds(self, namelist: list) -> Response.data:
        """
        get the System-IDs for given Names
        :param namelist: str
        :return: Response.data
        """
        return self._getResponse("post_universe_ids", None, names=namelist)

    def getSystemNames(self, idlist: list) -> Response.data:
        """
        get the System-Names based on System-IDs
        :param idlist: int
        :return: Response.data
                 format is [{"category": xx, "name": xx, "id": xx} ...]
        """
        return self._getResponse("post_universe_names", None, ids=idlist)

    def getKills(self) -> Response.data:
        """
        retrieve the number of Kills per system since downtime
        :return: Response.data
                 format is [{"npc_kills": xx, "pod_kills": xx, "ship_kills": xx, ""system_id": xx} ...]
        """
        return self._getResponse("get_universe_system_kills", None)

    def getJumps(self) -> Response.data:
        """
        retrieve the Number of jumps in the Universe since downtime
        :return: Response.data
                 format is [{"ship_jumps": xx, "system_id": xx} ...]
        """
        return self._getResponse("get_universe_system_jumps", None)

    def getShipGroups(self) -> Response.data:
        """
        retrieve a list of Ship-Groups based on Universe-Category 6
        :return: Response.data
                 format is [{"ship_jumps": xx, "system_id": xx} ...]
         """
        return self._getResponse(
            "get_universe_categories_category_id", None, category_id=6
        )

    def getShipGroupTypes(self, groupid: int) -> Response.data:
        """
        retrieve a list of Ship-Items in a given group
        :param groupid:
        :return: Response.data
                 format is [{"ship_jumps": xx, "system_id": xx} ...]
        """
        return self._getResponse("get_universe_groups_group_id", None, group_id=groupid)

    def getShip(self, shipid: int) -> Response.data:
        """
        retrieve a Ship-Item
        :param shipid:
        :return: Response.data
                 format is [{"ship_jumps": xx, "system_id": xx} ...]
         """
        return self._getResponse("get_universe_types_type_id", None, type_id=shipid)

    @property
    def getShipList(self) -> list:
        """
        Property to return a valid list of ships
        :return: List
        """
        ships = []
        cacheKey = "_".join(("esicache", "getshiplist"))
        ships = self.cache.get(cacheKey)
        try:
            if ships is None or len(ships) == 0:
                self.LOGGER.debug("Loading Ship-Data...")
                ships = []
                shipgroup = self.getShipGroups()
                for group in shipgroup["groups"]:
                    shiptypes = self.getShipGroupTypes(group)
                    for ship in shiptypes["types"]:
                        shipitem = self.getShip(ship)
                        ships.append(shipitem)
                self.cache.set(cacheKey, ships)
                self.LOGGER.debug("Loading Ship-Data...complete")
        except Exception as e:
            self.cache.invalidate(cacheKey)
            self.LOGGER.error("Error retrieving Ship-List from ESI", e)
            raise
        return ships

    def currentEveTime(self) -> datetime.datetime:
        """
        Returns the current eve-time as a datetime.datetime
        """
        return datetime.datetime.utcnow()

    def secondsTillDowntime(self) -> int:
        """
        Return the seconds till the next downtime
        """
        now = self.currentEveTime()
        target = now
        if now.hour > 11:
            target = target + datetime.timedelta(1)
        target = datetime.datetime(target.year, target.month, target.day, 11, 0, 0, 0)
        delta = (target - now).total_seconds()
        return int(delta)


if __name__ == "__main__":
    import sys
    # from PyQt5.QtWidgets import QApplication
    #
    # app = QApplication(sys.argv)

    interface = EsiInterface(ignore_security=False)
    print(interface.currentEveTime())
    # app.exec_()
