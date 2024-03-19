from pageserver.views.generic import *
from pageserver.views.base import Consumer
from pageserver.cache import *
from pageserver.conf import settings
from pageserver.cache import cache
from pageserver.utils import asynctools
from pageserver.utils.time import get_datetime_display, bj_now
from pageserver.utils.gmsm.sm4 import SM4
from pageserver.utils.base85 import a85decode, a85encode
from pageserver.utils.byteslib import utf8encode, utf8decode, hex2bytes
from pageserver.utils.process import shell
from pageserver.utils.generic import get_obj
from ..model import AdminAccount
from ..secrets import Secrets, decrypt, encrypt
import os
import sys
import json
import asyncio


class IndexView(TemplateView):
    use_cache = True

    def get_template_name(self):
        basedir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        path = os.path.join(basedir, 'templates', 'admin.html')
        return path

    async def get_template(self):
        cls = self.__class__
        if cls._template:
            return cls._template

        html = await asynctools.file(self.get_template_name(), mode='r')
        html = html.format(Secrets.public_key(True))
        html = html.encode('utf-8')
        if self.use_cache:
            cls._template = html

        return html
async def get_connect_info(params):
    now = get_datetime_display(bj_now())
    database = {}
    for k in settings.DATABASE:
        d = settings.DATABASE[k]
        database[k] = {
            'engine': d['engine']
        }

    data = {
        'TOTAL_CONNECT': GLOBAL.TOTAL_CONNECT,
        'TOTAL_REQUEST': GLOBAL.TOTAL_REQUEST,
        'BAD_REQUEST': GLOBAL.BAD_REQUEST,
        'VALID_REQUEST': GLOBAL.VALID_REQUEST,
        'STATIC_REQUEST': GLOBAL.STATIC_REQUEST,
        'CURRENT_CONNECT': GLOBAL.CURRENT_CONNECT,
        'database': database,
    }

    return {'info': data, 'now': now}



async def get_memory_info(params):
    res = None
    now = get_datetime_display(bj_now())
    if sys.platform.startswith('linux'):
        res = os.popen("free -h").readlines()
        res += os.popen("df -h").readlines()
    return {'info': res, 'now': now}


async def get_media_size(kwargs):
    res = '-'
    now = get_datetime_display(bj_now())
    path = settings.MEDIA_DIR
    if os.path.exists(path):
        if sys.platform.startswith('linux'):
            res = os.popen(f"du -sh {path}").readlines()[0].split("\t")[0]
    return {'size': res, 'now': now}

async def get_top_info(kwargs):
    res = None
    now = get_datetime_display(bj_now())
    if sys.platform.startswith('linux'):
        stdout, stderr = await shell('top -b -n 1')
        if stdout:
            res = stdout.decode().split('\n')[:20]

    return {'info': res, 'now': now}


ROUTER = {
    "/media/size": get_media_size,
    "/memory/info": get_memory_info,
    "/connect/info": get_connect_info,
    "/top/info": get_top_info,
}


class OnlineConsumer(Consumer):
    def decrypt(self, msg):
        msg = a85decode(msg)
        msg = self.sm4.decrypt(msg)
        msg = json.loads(utf8decode(msg))
        return msg

    def encrypt(self, msg):
        msg = json.dumps(msg)
        msg = utf8encode(msg)
        msg = self.sm4.encrypt(msg)
        msg = a85encode(msg)
        return msg

    async def handshake(self):
        once = self.request.GET.get('login')
        if data := cache.get(once):
            if obj := get_obj(AdminAccount, data['pk']):
                cache.delete(once)
                self.request.admin = obj
                self.sm4 = SM4(hex2bytes(data['sm4']))
                self.bad = 0
                return True

        return False

    async def onopen(self):
        pass

    async def onmessage(self, text_data=None, bytes_data=None):
        try:
            msg = self.decrypt(text_data)
            res = {
                'uri': msg['uri'],
                'res': await ROUTER[msg['uri']](msg['_'])
            }
            await self.send(self.encrypt(res))
        except Exception as e:
            self.bad += 1
            await self.send("404")
            if self.bad > 10:
                await self.close()

    async def onchannel(self, text_data=None, bytes_data=None):
        pass

    async def onclose(self):
        pass


if __name__ == "__main__":
    print(get_top_info(None))