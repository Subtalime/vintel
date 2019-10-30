from ..cache import Cache
from ..resources import getVintelDir
from esipy.cache import BaseCache
import hashlib, os

try:
    import pickle
except ImportError:  # pragma: no cover
    import cPickle as pickle


def _hash(data):
    """ generate a hash from data object to be used as cache key """
    hash_algo = hashlib.new('md5')
    hash_algo.update(pickle.dumps(data))
    # prefix allows possibility of multiple applications
    # sharing same keyspace
    return 'esi_' + hash_algo.hexdigest()


class EsiCache(BaseCache):
    def __init__(self):
        Cache.PATH_TO_CACHE = os.path.join(getVintelDir(), "esi_cache.sqlite3")
        self.cache = Cache(forceVersionCheck=True)

    def get(self, key, default=None):
        value = self.cache.getFromCache(_hash(key))
        return pickle.loads(value) if value is not None else default

    def set(self, key, value):
        self.cache.putIntoCache(_hash(key), pickle.dumps(value))

    def invalidate(self, key):
        self.cache.delFromCache(_hash(key))

    def invalidateAll(self):
        with Cache.SQLITE_WRITE_LOCK:
            query = "DELETE FROM cache"
            self.cache.con.execute(query)
            self.cache.con.commit()


