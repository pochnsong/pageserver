import time
import asyncio
from redis import asyncio as aioredis
import json


class Wrapper:
    @staticmethod
    def get_channel_name( channel):
        return f"channel.{channel}"

    @staticmethod
    def get_group_name(group):
        return f"group.{group}"

    @staticmethod
    def serialize(text_data=None, bytes_data=None):
         return json.dumps({
             'type': 'channel', 'text': text_data, 'bytes': bytes_data
         })

    @staticmethod
    def deserialize(message):
        return json.loads(message)


class RedisLayer(object):
    """
    Redis channel layer.

    It routes all messages into remote Redis server. Support for
    sharding among different Redis installations and message
    encryption are provided.
    """
    def __init__(self):
        self.capacity = 1024
        self.expiry = 3600
        self.redis = None
        self.host = None
        self.db = 0

    async def setup(self, host, port, db=0, **kwargs):
        self.host = (host, port)
        self.db = db
        self.redis = aioredis.from_url(host, port=port, db=db)

    async def send(self, channel, text_data=None, bytes_data=None):
        """
        Send a message onto a (general or specific) channel.
        """
        channel = Wrapper.get_channel_name(channel)
        await self.redis.rpush(channel, Wrapper.serialize(text_data, bytes_data))

    async def receive(self, channel):
        channel = Wrapper.get_channel_name(channel)
        conn = aioredis.from_url(self.host[0], port=self.host[1], db=self.db)
        _, data = await conn.blpop(channel)
        #await conn.close()
        data = Wrapper.deserialize(data)
        return data

    async def unbind(self, channel):
        """解绑 receive"""
        channel = Wrapper.get_channel_name(channel)
        await self.redis.delete(channel)

    async def clean(self):
        """解绑 receive"""
        await self.redis.flushdb()

    async def group_join(self, group, channel):
        """
        Adds the channel name to a group.
        """
        group = Wrapper.get_group_name(group)
        await self.redis.zadd(group, {channel: time.time()})

    async def group_discard(self, group, channel):
        group = Wrapper.get_group_name(group)
        await self.redis.zrem(group, channel)

    async def group_members(self, group):
        """获取 group 中的成员"""
        group = Wrapper.get_group_name(group)
        return [x.decode('utf-8') for x in await self.redis.zrange(group, 0, -1)]

    async def group_send(self, group, text_data=None, bytes_data=None):
        """
        Sends a message to the entire group.
        """
        for channel in await self.group_members(group):
            await self.send(channel, text_data, bytes_data)






