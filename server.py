from pageserver.http.request import Request
from pageserver.http.response import Http500, JsonResponse
from pageserver.http.exception import Error
from pageserver.utils import log, time
from pageserver.cache import *
import socket
import types
import asyncio
import os
import sys

class PageServer(object):
    read_chuck_size = 1024
    write_chuck_size = 1024

    def __init__(self, app, address="127.0.0.1", port=8000, ssl_context=None):
        self.server = None
        self.address = address
        self.port = port
        self.conns_ws = {}
        self.app = app
        self.loop = None
        self.ssl_context = ssl_context
    @classmethod
    async def close(cls, writer):
        try:
            writer.close()
            await writer.wait_closed()
        except:
            pass

    async def handle_http(self, request, writer):
        try:
            response = await self.app.http_process(request)
        except Error as e:
            response = JsonResponse({'status': 'FAIL', 'errors': str(e)})
        except Exception as e:
            log.error(e)
            response = Http500()

        await response.write(writer)
        log.log(request.method, request.path, response.status_code)
        return 'keep-alive' in request.META['connection']

    async def request_handle(self, reader, writer):
        GLOBAL.TOTAL_CONNECT += 1
        GLOBAL.CURRENT_CONNECT += 1

        try:
            while True:
                GLOBAL.TOTAL_REQUEST += 1
                header = await reader.readuntil(b'\r\n\r\n')
                request = Request(header)
                await request.setup(reader)
                GLOBAL.VALID_REQUEST += 1

                if 'sec-websocket-version' in request.META:
                    await self.app.ws_process(request, reader, writer)
                    break

                keep_alive = await self.handle_http(request, writer)

                if not keep_alive:
                    pass
                break

        except Exception as e:
            GLOBAL.BAD_REQUEST += 1
        finally:
            await self.close(writer)

        GLOBAL.CURRENT_CONNECT -= 1
        print("close")

    async def _start(self, init_func=None):
        await self.app.setup()
        if callable(init_func):
            await init_func()

        reuse_port = os.name == "posix"
        protocol = "https" if self.ssl_context else 'http'
        print("服务器 {}://{}:{}".format(protocol, self.address, self.port))
        self.server = await asyncio.start_server(
            self.request_handle, host=self.address, port=self.port,
            family=socket.AF_INET, backlog=128, reuse_address=True,
            reuse_port=reuse_port, start_serving=True, ssl=self.ssl_context)
        GLOBAL.START_TIME = time.bj_now()
    def start(self, init_func=None):
        this_python = sys.version_info[:2]
        min_version = (3, 11)

        if this_python < min_version:
            print(f"the min version is python{min_version[0]}.{min_version[1]}, current: {sys.version}")
            exit(1)

        self.loop = asyncio.new_event_loop()
        self.loop.run_until_complete(self._start(init_func))
        self.loop.run_forever()
