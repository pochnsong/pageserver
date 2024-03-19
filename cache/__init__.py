class Cache(object):
    _alias = {}

    @classmethod
    def create_engine(cls, **kwargs):
        if kwargs['engine'] == "redis":
            from .backend.redis_cache import RedisCache
            r = RedisCache()
            r.setup(**kwargs)
            return r

        if kwargs['engine'] == "memory":
            from .backend.memory_cache import MemoryCache
            r = MemoryCache()
            return r

    def setup(self, config):
        for k, v in config.items():
            self._alias[k] = self.create_engine(**v)

    def delete(self, name, alias="default"):
        self._alias[alias].delete(name)

    def set(self, name, value, timeout=60, alias="default"):
        self._alias[alias].set(name, value, timeout)

    def get(self, name, default=None, alias="default"):
        return self._alias[alias].get(name)

    def reset(self, name, value, alias="default"):
        return self._alias[alias].reset(name, value)

    def ttl(self, name, alias="default"):
        return self._alias[alias].ttl(name)

    def expire(self, name, seconds, alias="default"):
        """设置过期时间"""
        return self._alias[alias].expire(name, seconds)

    def list_add(self, name, value, alias="default"):
        self._alias[alias].list_add(name, value)

    def list_rm(self, name, value, alias="default"):
        self._alias[alias].list_rm(name, value)

    def list_get(self, name, alias="default"):
        return self._alias[alias].list_get(name)

    def flag_items(self, name, alias="default"):
        return self._alias[alias].flag_items(name)

    def flag_add(self, name, key, value=1, alias="default"):
        return self._alias[alias].flag_add(name, key, value)

    def flag_set(self, name, key, value=1, alias="default"):
        return self._alias[alias].flag_set(name, key, value)

    def flag_get(self, name, key, alias="default"):
        return self._alias[alias].flag_get(name, key)

    def keys(self, cursor=0, alias="default") -> (int, list):
        """获取所有的keys"""
        return self._alias[alias].keys(cursor)

    def size(self, alias="default") -> int:
        return self._alias[alias].size()

    def get_type(self, key: str, alias="default") -> str:
        return self._alias[alias].get_type(key)

    def __getitem__(self, item):
        return self._alias[item]


class GLOBAL:
    TOTAL_CONNECT = 0  # 累计连接
    TOTAL_REQUEST = 0  # 累计请求
    BAD_REQUEST = 0  # 坏请求
    VALID_REQUEST = 0  # 有效请求
    STATIC_REQUEST = 0  # 静态请求
    CURRENT_CONNECT = 0  # 当前连接
    START_TIME = None


cache = Cache()

__all__ = ["cache", "GLOBAL"]
