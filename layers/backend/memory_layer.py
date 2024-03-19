import asyncio

class InMemoryLayer(object):
    """
    In-memory channel layer implementation
    """

    def __init__(self):
        self.channels = {}
        self.groups = {}
        self.capacity = 1024
        self.expiry = 3600

    async def send(self, channel, text_data=None, bytes_data=None):
        queue = self.channels.setdefault(channel, asyncio.Queue())
        if queue.qsize() >= self.capacity:
            raise Exception(channel)

        await queue.put((text_data, bytes_data))

    async def receive(self, channel):

        queue = self.channels.setdefault(channel, asyncio.Queue())

        text_data, bytes_data = await queue.get()
        if queue.empty():
            del self.channels[channel]

        return {'type': 'channel', 'name': channel, 'text': text_data, 'bytes': bytes_data}

    async def unbind(self, channel):
        """解绑 receive"""
        try:
            del self.channels[channel]
        except:
            pass

    async def clean(self):
        """解绑 receive"""
        self.channels = {}
        self.groups = {}

    async def group_join(self, group, channel):
        """
        Adds the channel name to a group.
        """
        if group not in self.groups:
            self.groups[group] = []
        self.groups[group].append(channel)

    async def group_discard(self, group, channel):
        if group in self.groups:
            if channel in self.groups[group]:
                self.groups[group].remove(channel)
            if not self.groups[group]:
                del self.groups[group]

    async def group_members(self, group):
        """获取 group 中的成员"""
        return self.groups.get(group, [])

    async def group_send(self, group, text_data=None, bytes_data=None):
        # Send to each channel
        for channel in await self.group_members(group):
            try:
                await self.send(channel, text_data, bytes_data)
            except Exception as e:
                pass
