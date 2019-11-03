#   Vintel - Visual Intel Chat Analyzer
#   Copyright (c) 2019. Steven Tschache (github@tschache.com)
#  #
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#  #
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	 See the
#   GNU General Public License for more details.
#  #
#   You should have received a copy of the GNU General Public License
#   along with this program.	 If not, see <http://www.gnu.org/licenses/>.
#  #
#  #
#

from ..cache.dbstructure import updateDatabase
from ..resources import getVintelDir
from esipy.cache import BaseCache
import hashlib, os, threading
import pickle, sqlite3
from ast import literal_eval

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

    def __init__(self):
        if self.BASE_DIR:
            self.dbPath = os.path.join(self.BASE_DIR, "esi_cache.sqlite3")
        else:
            self.dbPath = os.path.join(getVintelDir(), "esi_cache.sqlite3")
        self.con = sqlite3.connect(self.dbPath)
        with EsiCache.SQLITE_WRITE_LOCK:
            self.checkVersion()
        EsiCache.VERSION_CHECKED = True

    def checkVersion(self):
        query = "SELECT version FROM version;"
        version = 0
        try:
            version = self.con.execute(query).fetchall()[0][0]
        except Exception as e:
            if (isinstance(e, sqlite3.OperationalError) and "no such table: version" in str(e)):
                pass
            elif (isinstance(e, IndexError)):
                pass
            else:
                raise e
        updateDatabase(version, self.con)

    def get(self, key, default=None):
        """ Getting a value from cache
             key = the key for the value
             outdated = returns the value also if it is outdated
         """
        try:
            query = "SELECT key, data FROM cache WHERE key = ?"
            founds = self.con.execute(query, (_hash(key),)).fetchall()
            if founds is None or len(founds) == 0:
                return default
            value = founds[0][1]
            return literal_eval(value)
        except ValueError as e:
            if isinstance(value, bytes):
                return pickle.loads(value)
            return value
        except SyntaxError as e:
            return value
        except Exception as e:
            raise


    def set(self, key, value):
        with EsiCache.SQLITE_WRITE_LOCK:
            try:
                query = "DELETE FROM cache WHERE key = ?"
                self.con.execute(query, (_hash(key),))
                query = "INSERT INTO cache (key, data) VALUES (?, ?)"
                v = str(value)
                self.con.execute(query, (_hash(key), v))
                self.con.commit()
            except Exception as e:
                raise

    def invalidate(self, key):
        with EsiCache.SQLITE_WRITE_LOCK:
            try:
                query = "DELETE FROM cache WHERE key = ?"
                self.con.execute(query, (_hash(key),))
                self.con.commit()
            except Exception as e:
                raise

    def invalidateAll(self):
        with EsiCache.SQLITE_WRITE_LOCK:
            try:
                query = "DELETE FROM cache"
                self.con.execute(query)
                self.con.commit()
            except Exception as e:
                raise


