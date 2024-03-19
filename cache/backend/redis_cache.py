from pageserver.utils.data_struct import Wrapper
import time
import redis


class RedisCache(object):
    """
    Redis Cache.
    """
    def __init__(self):
        self.redis = None

    def get_conn(self):
        return self.redis

    def setup(self, host, port, db=0, **kwargs):
        self.redis = redis.StrictRedis(host, port=port, db=db)

    def delete(self, name):
        self.redis.delete(name)

    def set(self, name, value, timeout=60):
        self.redis.set(name, Wrapper.serialize(value), ex=timeout)

    def get(self, name):
        value = self.redis.get(name)
        if value is None:
            return None
        return Wrapper.deserialize(value)

    def reset(self, name, value):
        timeout = self.redis.ttl(name)
        self.redis.set(name, Wrapper.serialize(value), ex=timeout)

    def ttl(self, name):
        return self.redis.ttl(name)

    def expire(self, name, seconds):
        return self.redis.expire(name, seconds)

    def list_add(self, name, value):
        self.redis.rpush(name, value)

    def list_rm(self, name, value):
        self.redis.lrem(name, 0, value)

    def list_get(self, name):
        self.redis.lrange(name, 0, -1)

    def flag_items(self, name):
        data = self.redis.hgetall(name)
        res = {}
        for k, v in data.items():
            res[k.decode('utf-8')] = v.decode('utf-8')
        return res

    def flag_add(self, name, key, value):
        self.redis.hincrby(name, key, value)

    def flag_set(self, name, key, value):
        self.redis.hset(name, key, value)

    def flag_get(self, name, key):
        self.redis.hget(name, key)

    def keys(self, skip=0) -> (int, list):
        next_skip, data = self.redis.scan(skip)
        return next_skip, [x.decode('utf-8') for x in data]

    def size(self) -> int:
        return self.redis.dbsize()

    def get_type(self, key: str) -> str:
        return self.redis.type(key).decode('utf-8')

