import time
import sys

class MemoryCache(object):
    """
    Memory Cache.
    note! the cache value will lose when server stop
    """
    def __init__(self):
        self._data = {}
        self._expire = {}

    def delete(self, name):
        if name in self._data:
            del self._data[name]
        if name in self._expire:
            del self._expire[name]

    def set(self, name, value, timeout=60):
        self._data[name] = value
        if timeout is not None:
            self._expire[name] = int(time.time())+timeout

    def get(self, name):
        value = self._data.get(name)
        ex = self._expire.get(name)

        if ex is not None:
            now = int(time.time())
            if now > ex:
                self.delete(name)
                return None

        if value is None:
            return None

        return value

    def reset(self, name, value):
        self._data[name] = value

        if name in self._expire:
            ex = self._expire[name]
            now = int(time.time())
            if now > ex:
                self.delete(name)

    def ttl(self, name: str) -> int:
        """time to live"""
        ex = self._expire.get(name)

        res = -1

        if ex is not None:
            res = ex - int(time.time())
            if res < 0:
                self.delete(name)
                res = -2

        return res

    def expire(self, name, seconds):
        self._expire[name] = int(time.time())+seconds

    def list_add(self, name, value):
        if name not in self._data:
            self._data[name] = list()
        self._data[name].append(value)

    def list_rm(self, name, value):
        self._data[name].remove(value)

    def list_get(self, name: str) -> list:
        return self._data[name]

    def flag_items(self, name: str) -> dict:
        return self._data[name]

    def flag_add(self, name, key, value):
        if name not in self._data:
            self._data[name] = {}

        if key not in self._data[name]:
            self._data[name][key] = 0

        self._data[name][key] += value

    def flag_set(self, name, key, value):
        if name not in self._data:
            self._data[name] = {}

        self._data[name][key] = value

    def flag_get(self, name, key):
        if name in self._data:
            self._data[name].get(key)

    def keys(self, skip=0) -> (int, list):
        return 0, list(self._data.keys())

    def size(self) -> int:
        return sys.getsizeof(self._data)

    def get_type(self, key: str) -> str:
        val = self._data[key]
        if isinstance(val, str):
            return "string"

        if isinstance(val, list):
            return "list"

        if isinstance(val, set):
            return "set"

        if isinstance(val, dict):
            return "hash"

        return "-"
