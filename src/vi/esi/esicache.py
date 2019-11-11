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

from esipy.cache import BaseCache
import hashlib
import os
import threading
import sys
import pickle
import sqlite3
import time
from ast import literal_eval

"""
you can add external databaseupdates to database updates.
they should be a tuple like (query, condition)
query	  = the query to run on the database connection
condition = if TRUE the query qull be executed
"""
databaseUpdates = []


def updateDatabase(oldVersion, con):
    """ Changes for the database-structure should be added here,
        or added to added_database_updates
        con = the database connection
    """
    queries = []
    if oldVersion < 1:
        queries += ["CREATE TABLE version (version INT)", "INSERT INTO version (version) VALUES (1)"]
    if oldVersion < 2:
        queries += ["CREATE TABLE playernames (charname VARCHAR PRIMARY KEY, status INT, modified INT)",
                    "CREATE TABLE avatars (charname VARCHAR PRIMARY KEY, data  BLOB, modified INT)",
                    "UPDATE version SET version = 2"]
    if oldVersion < 3:
        queries += ["CREATE TABLE cache (key VARCHAR PRIMARY KEY, data BLOB, modified INT, maxage INT)",
                    "UPDATE version SET version = 3"]
    for query in queries:
        con.execute(query)
    for update in databaseUpdates:
        if update[1]:
            con.execute(update[0])
    con.commit()

def _hash(data):
    """ generate a hash from data object to be used as cache key """
    hash_algo = hashlib.new('md5')
    hash_algo.update(pickle.dumps(data))
    # prefix allows possibility of multiple applications
    # sharing same keyspace
    return 'esi_' + hash_algo.hexdigest()


class EsiCache(BaseCache):
    # Ok, this is dirty. To make sure we check the database only
    # one time/runtime we will change this classvariable after the
    # check. Following inits of Cache will now, that we allready checked.
    VERSION_CHECKED = False
    BASE_DIR = None
    # Cache-Instances in various threads: must handle concurrent writings
    SQLITE_WRITE_LOCK = threading.Lock()
    # default 3 days for ESI values
    MAX_AGE = 60 * 60 * 24 * 3

    def __init__(self, enable_cache: bool = True):
        self.__cache_enabled = enable_cache
        if not self.__cache_enabled:
            return
        if self.BASE_DIR:
            self.dbPath = os.path.join(self.BASE_DIR, "esi_cache.sqlite3")
        else:
            base_path = os.path.abspath(".")
            if getattr(sys, 'frozen', False):
                base_path = sys._MEIPASS
            self.dbPath = os.path.join(base_path, "esi_cache.sqlite3")
        try:
            self.con = sqlite3.connect(self.dbPath, check_same_thread=False)
            with EsiCache.SQLITE_WRITE_LOCK:
                self.checkVersion()
            EsiCache.VERSION_CHECKED = True
        except Exception as e:
            raise FileNotFoundError("Unable to access DB at \"%s\"" % self.dbPath, e)

    def checkVersion(self):
        if not self.__cache_enabled:
            return
        version = 0
        try:
            query = "SELECT version FROM version;"
            version = self.con.execute(query).fetchall()[0][0]
        except Exception as e:
            if (isinstance(e, sqlite3.OperationalError) and "no such table: version" in str(e)):
                pass
            elif (isinstance(e, IndexError)):
                pass
            else:
                raise e
        updateDatabase(version, self.con)

    def getFromCache(self, key, outdated=False, default=None):
        return self.get(key, outdated, default)

    # outdated defaults to True, because it may contain ESI refresh tokens
    def get(self, key, outdated=True, default=None):
        """ Getting a value from cache
             key = the key for the value
             outdated = returns the value also if it is outdated
         """
        if not self.__cache_enabled:
            return default
        try:
            query = "SELECT key, data, modified, maxage FROM cache WHERE key = ?"
            founds = self.con.execute(query, (_hash(key),)).fetchall()
            if founds is None or len(founds) == 0:
                return default
            elif founds[0][3] and founds[0][2] + founds[0][3] < time.time() and not outdated:
                return default
            value = founds[0][1]
            return pickle.loads(value)
        except (ValueError, TypeError):
            try:
                return literal_eval(value)
            except Exception:
                return value
        except SyntaxError:
            try:
                return literal_eval(value)
            except Exception:
                return value
        except Exception as e:
            raise e

    def putIntoCache(self, key, value, max_age=None):
        self.set(key, value, max_age)

    def set(self, key, value, max_age=None):
        if not self.__cache_enabled:
            return
        # some of the Esi-Data don't have  __getattr__ (which pickle requires)
        try:
            store_value = pickle.dumps(value)
        except KeyError:
            # if that's the case, we store as String
            store_value = str(value)
        with EsiCache.SQLITE_WRITE_LOCK:
            try:
                query = "DELETE FROM cache WHERE key = ?"
                self.con.execute(query, (_hash(key),))
                if not max_age:
                    max_age = EsiCache.MAX_AGE
                query = "INSERT INTO cache (key, data, modified, maxage) VALUES (?, ?, ?, ?)"
                self.con.execute(query, (_hash(key), store_value, time.time(), max_age))
                self.con.commit()
            except Exception as e:
                raise e

    def delFromCache(self, key):
        self.invalidate(key)

    def invalidate(self, key):
        if not self.__cache_enabled:
            return
        with EsiCache.SQLITE_WRITE_LOCK:
            try:
                query = "DELETE FROM cache WHERE key = ?"
                self.con.execute(query, (_hash(key),))
                self.con.commit()
            except Exception as e:
                raise e

    def invalidateAll(self):
        if not self.__cache_enabled:
            return
        with EsiCache.SQLITE_WRITE_LOCK:
            try:
                query = "DELETE FROM cache"
                self.con.execute(query)
                self.con.commit()
            except Exception as e:
                raise e
