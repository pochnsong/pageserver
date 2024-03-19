from pageserver.utils.asynctools import async_to_sync
__all__ = ["layer"]


class Layer(object):
    _layers = {}

    @classmethod
    async def create_engine(cls, **kwargs):
        if kwargs['engine'] == "memory":
            from .backend import memory_layer
            return memory_layer.InMemoryLayer()
        if kwargs['engine'] == "redis":
            from .backend.redis_layer import RedisLayer
            r = RedisLayer()
            await r.setup(**kwargs)
            return r

    async def setup(self, config):
        for k, v in config.items():
            self._layers[k] = await self.create_engine(**v)

    def get(self, item="default"):
        return self._layers.get(item)

    def __getitem__(self, item="default"):
        return self._layers[item]


layer = Layer()
