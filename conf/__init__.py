import importlib
from pageserver.db import database
from pageserver.cache import cache
from pageserver.layers import layer
from pageserver.conf import default


class Settings(object):

    def __init__(self):

        for k in dir(default):
            if k.isupper():
                v = getattr(default, k)
                setattr(self, k, v)

    async def setup(self, user_settings=None):
        if user_settings:
            for k in dir(user_settings):
                if k.isupper():
                    _v = getattr(self, k, None)
                    v = getattr(user_settings, k)
                    if isinstance(_v, dict):
                        _v.update(v)
                    else:
                        setattr(self, k, v)

        if hasattr(self, 'DATABASE'):
            database.setup(self.DATABASE)

        if hasattr(self, 'CACHE'):
            cache.setup(self.CACHE)

        if hasattr(self, 'LAYER'):
            await layer.setup(self.LAYER)

        #print("setup", self)


settings = Settings()
