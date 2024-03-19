from pageserver.http.response import Http405
from pageserver.http.response import JsonResponse, HttpResponse
from pageserver.http.websocket import WebSocket, OPCODE, WebSocketCloseException
from pageserver.utils.asynctools import await_many_dispatch, cancel_tasks, sync_to_async, TaskGroup
from pageserver.layers import layer
import functools
import inspect
import types
import uuid
import asyncio


class View(object):
    use_thread = False  # 使用新进程运行

    def __init__(self, request):
        self.request = request

    @classmethod
    async def as_view(cls, request, **kwargs):
        view = cls(request)
        func = getattr(view, request.method.lower())
        if not func:
            return Http405()

        if not inspect.iscoroutinefunction(func):
            if view.use_thread:
                return await asyncio.to_thread(func, request, **kwargs)

            func = functools.partial(sync_to_async, func)

        return await func(request, **kwargs)


class Consumer(object):
    layer_alias = "default"

    """handshake->onopen->onmessage->onclose"""
    def __init__(self, request, reader, writer, **kwargs):
        self.request = request
        self.kwargs = kwargs
        self.reader = reader
        self.writer = writer
        self.channel = f'ol@{uuid.uuid4().hex}'
        self.layer = layer.get(self.layer_alias)
        self.tg = None

    async def handshake(self):
        return True

    async def onopen(self):
        pass

    async def onmessage(self, text_data=None, bytes_data=None):
        pass

    async def onchannel(self, text_data=None, bytes_data=None):
        pass

    async def onclose(self):
        pass

    def add_task(self, task):
        self.tg.create_task(task)

    async def group_members(self, name):
        return await self.layer.group_members(name)

    async def group_join(self, name):
        """将频道加入分组"""
        await self.layer.group_join(name, self.channel)

    async def group_send(self, name, text_data=None, bytes_data=None):
        await self.layer.group_send(name, text_data, bytes_data)

    async def group_discard(self, group_name):
        """离开group"""
        await self.layer.group_discard(group_name, self.channel)

    async def receive(self, message):
        if message['type'] == "ping":
            return await WebSocket.send(self.writer, OPCODE.PONG)

        if message['type'] == "websocket":
            return await self.onmessage(message['text'], message['bytes'])

        if message['type'] == "channel":
            return await self.onchannel(message['text'], message['bytes'])

    async def send(self, text_data=None, bytes_data=None):
        if text_data is not None:
            await WebSocket.send(self.writer, OPCODE.TEXT, text_data)
        if bytes_data is not None:
            await WebSocket.send(self.writer, OPCODE.BYTES, bytes_data)

    async def close(self):
        await WebSocket.close(self.writer)

    async def _listen_websocket(self):
        try:
            while True:
                message = await WebSocket.receive(self.reader)
                await self.receive(message)
        except asyncio.CancelledError:
            pass

    async def _listen_channel(self):
        try:
            while True:
                message = await self.layer.receive(self.channel)
                await self.receive(message)
        except asyncio.CancelledError:
            pass

    async def wait(self):
        try:
            await self.onopen()
            async with TaskGroup() as tg:
                self.tg = tg
                tg.create_task(self._listen_websocket())
                if self.layer:
                    tg.create_task(self._listen_channel())
        finally:
            await WebSocket.disconnect(self.writer)
            await self.layer.unbind(self.channel)
            await self.onclose()

    @classmethod
    async def as_view(cls, request, reader, writer, **kwargs):
        self = cls(request, reader, writer, **kwargs)
        if await self.handshake():
            await WebSocket.handshake(self.request, self.writer)
            await self.wait()
        else:
            await self.close()


__all__ = [
    "View",
    "Consumer",
]
