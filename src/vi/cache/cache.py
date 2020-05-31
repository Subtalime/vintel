###########################################################################
#  Vintel - Visual Intel Chat Analyzer									  #
#  Copyright (C) 2014-15 Sebastian Meyer (sparrow.242.de+eve@gmail.com )  #
#																		  #
#  This program is free software: you can redistribute it and/or modify	  #
#  it under the terms of the GNU General Public License as published by	  #
#  the Free Software Foundation, either version 3 of the License, or	  #
#  (at your option) any later version.									  #
#																		  #
#  This program is distributed in the hope that it will be useful,		  #
#  but WITHOUT ANY WARRANTY; without even the implied warranty of		  #
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	 See the		  #
#  GNU General Public License for more details.							  #
#																		  #
#																		  #
#  You should have received a copy of the GNU General Public License	  #
#  along with this program.	 If not, see <http://www.gnu.org/licenses/>.  #
###########################################################################

import sqlite3
import threading
import time
import ast
import sys
import os
import logging
import pickle
from pathlib import Path
from .dbstructure import updateDatabase



def to_blob(x):
    return x
def from_blob(x):
    return x

class CacheError(BaseException):
    pass
class CacheWriteError(CacheError):
    pass
class CacheReadError(CacheError, KeyError):
    pass


class Cache(object):
    FOREVER = 60 * 60 * 24 * 365 * 10
    MAX_DEFAULT = 60 * 60 * 24 * 3
    # Cache checks PATH_TO_CACHE when init, so you can set this on a
    # central place for all Cache instances.
    PATH_TO_CACHE = None

    # Ok, this is dirty. To make sure we check the database only
    # one time/runtime we will change this classvariable after the
    # check. Following inits of Cache will now, that we allready checked.
    VERSION_CHECKED = False

    # Cache-Instances in various threads: must handle concurrent writings
    SQLITE_WRITE_LOCK = threading.Lock()
    DEFAULT_FILE = "cache.sqlite3"

    LOGGER = logging.getLogger(__name__)

    def __init__(self, path_to_sql_lite_file: str = DEFAULT_FILE, force_version_check: bool = False):
        """caching Class using Key-Value pairs.

        :param path_to_sql_lite_file: File-Path, Name and Extension to store the Cache-Data
        :type path_to_sql_lite_file: str
        :param force_version_check: upgrade the Database regardless of what version it represents
        :type force_version_check: bool
        """
        if Cache.PATH_TO_CACHE and not os.path.dirname(path_to_sql_lite_file):
            if os.path.basename(Cache.PATH_TO_CACHE).endswith("sqlite3"):
                path_to_sql_lite_file = Cache.PATH_TO_CACHE
            else:
                path_to_sql_lite_file = os.path.join(Cache.PATH_TO_CACHE, path_to_sql_lite_file)
        if not getattr(sys, 'frozen', False):  # we are running in DEBUG
            last_dot = path_to_sql_lite_file.rfind(".")
            path_to_sql_lite_file = path_to_sql_lite_file[:last_dot] + "_deb." + path_to_sql_lite_file[last_dot+1:]
        self.file_path = path_to_sql_lite_file
        self.version_check = force_version_check
        self.con = None
        self._connect()

    def _connect(self):
        if not self.con:
            try:
                self.con = sqlite3.connect(self.file_path, check_same_thread=False)
                if not Cache.VERSION_CHECKED or self.version_check:
                    with Cache.SQLITE_WRITE_LOCK:
                        self._check_version()
                Cache.VERSION_CHECKED = True
            except Exception as e:
                self.LOGGER.critical("Error creating Cache-File %s" % (self.file_path,), e)
                raise CacheError(e)

    def _check_version(self):
        query = "SELECT version FROM version;"
        version = 0
        try:
            version = self.con.execute(query).fetchall()[0][0]
        except Exception as e:
            if isinstance(e, sqlite3.OperationalError) and "no such table: version" in str(e):
                pass
            elif isinstance(e, IndexError):
                pass
            else:
                raise CacheError(e)
        updateDatabase(version, self.con)

    def put(self, key: str, value: object, maxAge = MAX_DEFAULT):
        """
        Putting something in the cache maxAge is maximum age in seconds
        """
        with Cache.SQLITE_WRITE_LOCK:
            try:
                query = "DELETE FROM cache WHERE key = ?"
                self.con.execute(query, (key,))
                query = "INSERT INTO cache (key, data, modified, maxAge) VALUES (?, ?, ?, ?)"
                self.con.execute(query, (key, value, time.time(), maxAge))
                self.con.commit()
            except Exception as e:
                self.LOGGER.error("Cache-Error put: %s -> %r" % (key, value, ), e)
                raise CacheWriteError(e)

    def delete(self, key: str):
        with Cache.SQLITE_WRITE_LOCK:
            try:
                query = "DELETE FROM cache WHERE key = ?"
                self.con.execute(query, (key,))
                self.con.commit()
            except Exception as e:
                self.LOGGER.error("Cache-Error delete: %s" % (key, ), e)
                raise CacheWriteError(e)

    def fetch(self, key, outdated=False, default=None):
        """
        Getting a value from cache
            key = the key for the value
            outdated = returns the value also if it is outdated
        """
        try:
            query = "SELECT key, data, modified, maxage FROM cache WHERE key = ?"
            founds = self.con.execute(query, (key,)).fetchall()
            if len(founds) == 0:
                return default
            elif founds[0][2] + founds[0][3] < time.time() and not outdated:
                return default
            else:
                return founds[0][1]
        except Exception as e:
            self.LOGGER.error("Cache-Error fetch: %s" % (key, ), e)
            raise CacheReadError(e)

    def put_player_name(self, name: str, status: str):
        """
        Putting a playername into the cache
        """
        with Cache.SQLITE_WRITE_LOCK:
            try:
                query = "DELETE FROM playernames WHERE charname = ?"
                self.con.execute(query, (name,))
                query = "INSERT INTO playernames (charname, status, modified) VALUES (?, ?, ?)"
                self.con.execute(query, (name, status, time.time()))
                self.con.commit()
            except Exception as e:
                self.LOGGER.error("Cache-Error put_player_name: %s, %s" % (name, status), e)
                raise CacheWriteError(e)

    def get_player_name(self, name: str):
        """
        Getting back infos about playername from Cache. Returns None if the name was
        not found, else it returns the status
        """
        name = ast.dump(str(name))
        selectquery = "SELECT charname, status FROM playernames WHERE charname = ?"
        founds = self.con.execute(selectquery, (name,)).fetchall()
        if len(founds) == 0:
            return None
        return founds[0][1]

    def put_avatar(self, name: str, data: object):
        """
        Put the picture of an player into the cache
        """
        with Cache.SQLITE_WRITE_LOCK:
            # data is a blob, so we have to change it to buffer
            try:
                data = to_blob(data)
                query = "DELETE FROM avatars WHERE charname = ?"
                self.con.execute(query, (name,))
                query = "INSERT INTO avatars (charname, data, modified) VALUES (?, ?, ?)"
                self.con.execute(query, (name, data, time.time()))
                self.con.commit()
            except Exception as e:
                self.LOGGER.error("Cache-Error put_avatar: %s, %r" % (name, data, ), e)
                raise CacheWriteError(e)

    def get_avatar(self, name: str):
        """
        Getting the avatars_pictures data from the Cache. Returns None if there is no
        entry in the cache
        """
        data = None
        try:
            selectQuery = "SELECT data FROM avatars WHERE charname = ?"
            founds = self.con.execute(selectQuery, (name,)).fetchall()
            if len(founds) != 0:
                # data is buffer, we convert it back to str
                data = from_blob(founds[0][0])
        except Exception as e:
            self.LOGGER.error("Cache-Error get_avatar: %s" % (name, ), e)
            raise CacheReadError(e)
        return data

    def delete_avatar(self, name: str):
        """
        Removing an avatar from the cache
        """
        try:
            with Cache.SQLITE_WRITE_LOCK:
                query = "DELETE FROM avatars WHERE charname = ?"
                self.con.execute(query, (name,))
                self.con.commit()
        except Exception as e:
            self.LOGGER.error("Cache-Error delete_avatar: %s" % (name, ), e)
            raise CacheWriteError(e)

    def put_jumpbridge_data(self, data: list):
        with Cache.SQLITE_WRITE_LOCK:
            try:
                cacheKey = "jumpbridge_data"
                query = "DELETE FROM cache WHERE key = ?"
                self.con.execute(query, (cacheKey,))
                query = "INSERT INTO cache (key, data, modified, maxAge) VALUES (?, ?, ?, ?)"
                self.con.execute(query, (cacheKey, pickle.dumps(data), time.time(), Cache.FOREVER))
                self.con.commit()
            except Exception as e:
                self.LOGGER.error("Cache-Error putJumpbridg: %r", (data, ), e)
                raise CacheWriteError(e)

    def fetch_jumpbridge_data(self) -> list:
        data = None
        try:
            cacheKey = "jumpbridge_data"
            query = "SELECT data FROM cache WHERE key = ?"
            founds = self.con.execute(query, (cacheKey,)).fetchall()
            if len(founds) > 0:
                data = pickle.loads(founds[0][0])
        except Exception as e:
            self.LOGGER.error("Cache-Error fetch_jumpbridge_data: %r" % (founds, ), e)
            raise CacheReadError(e)
        return data

    def delete_jumpbridge_data(self):
        try:
            cacheKey = "jumpbridge_data"
            with Cache.SQLITE_WRITE_LOCK:
                query = "DELETE FROM cache WHERE key = ?"
                self.con.execute(query, (cacheKey,))
                self.con.commit()
        except Exception as e:
            self.LOGGER.error("Cache-Error delete_jumpbridge_data", e)
            raise CacheWriteError(e)

    def save_settings(self, settings_identifier, object_setting, duration=FOREVER):
        import pickle
        store_value = pickle.dumps(object_setting)
        self.put(settings_identifier, store_value, duration)

    def recall_and_apply_settings(self, responder, settings_identifier):
        object_setting = self.fetch(settings_identifier)
        if object_setting:
            settings = pickle.loads(object_setting)
            for setting in settings:
                obj = responder if not setting[0] else getattr(responder, setting[0])
                # logging.debug("{0} | {1} | {2}".format(str(obj), setting[1], setting[2]))
                try:
                    getattr(obj, setting[1])(setting[2])
                except Exception as e:
                    self.LOGGER.error("{}: {} [{}]".format(__file__, e, setting[1]))
                    self.delete(settings_identifier)
                    raise CacheError(e)
