from pageserver.views.base import Consumer
from pageserver.views.tools import *
from pageserver.http.response import StreamResponse
from pageserver.http.exception import Error
from pageserver.utils.generic import get_obj
from .account import check_perm, AdminAccount
from datetime import datetime, date
import json
import time
import asyncio
import sys
config = __import__(settings.ADMIN['config'])


class UploadBlockFileAPI(UploadBlockAPI):
    def check_perm(self):
        return True

    @classmethod
    def temp_path(cls, cache_key):
        return os.path.join(settings.TEMP_DIR, cache_key)


def json_encode(obj):
    if isinstance(obj, datetime):
        return obj.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(obj, date):
        return obj.strftime("%Y-%m-%d")
    return obj


class BackupResponse(StreamResponse):
    def __init__(self, models):
        self.models = []
        for model_class in config.MODEL_LIST:
            if model_class.__name__ in models:
                self.models.append(model_class)

        self.skip = 0
        super().__init__(None, headers={"Content-Disposition": f"attachment;filename=bak"})

    def get_snapshot(self, model_class):
        columns = model_class.query().select("__all__").columns()
        count = model_class.query().count()
        res = {
            'name': model_class.__name__,
            'columns': columns,
            'count': count,
        }
        return json.dumps(res)

    def get_chunk(self, model_class, skip):
        res = model_class.query().skip(skip).limit(100).all(to='list')
        if res:
            res = json.dumps(res, ensure_ascii=False, default=json_encode)
        return res

    async def _write_line(self, writer, data):
        data = f"{data}\r\n".encode('utf-8')
        writer.write(f"{len(data):x}\r\n".encode("utf-8"))
        writer.write(data + b'\r\n')
        await writer.drain()

    async def write(self, writer):
        writer.write(bytes(self))
        await writer.drain()

        for model_class in self.models:
            await self._write_line(writer, "#"+model_class.__name__)

            data = await asyncio.to_thread(self.get_snapshot, model_class)
            await self._write_line(writer, data)

            skip = 0
            while True:
                data = await asyncio.to_thread(self.get_chunk, model_class, skip)
                if not data:
                    break
                await self._write_line(writer, data)
                skip += 100

        writer.write(b"0\r\n\r\n")
        await writer.drain()


class BackupExportView(API):
    def check_perm(self):
        try:
            login = self.request.GET['login']
            if data := cache.get(login):
                cache.delete(login)
                return True
        except:
            pass

    def post(self, request):
        models = request.POST.getlist("model")
        return BackupResponse(models)


class BackupImportAPI(Consumer):

    async def handshake(self):
        once = self.request.GET.get('login')
        if data := cache.get(once):
            cache.delete(once)
            if obj := get_obj(AdminAccount, data['pk']):
                return obj.is_super

        return False

    async def onopen(self):
        #print("open")
        pass

    async def onmessage(self, text_data=None, bytes_data=None):
        try:
            data = json.loads(text_data)
            fk = data['fk']
            script = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'tasks', 'reload_db.py')
            fname = UploadBlockFileAPI.temp_path(fk)
            proc = await asyncio.create_subprocess_exec(
                sys.executable,
                script,
                settings.BASE_DIR,
                fname,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE)

            while True:
                msg = await proc.stdout.readline()
                await self.send(msg)
                if msg == b'':
                    break

            await proc.wait()

        except Exception as e:
            await self.send(json.dumps({'errors': str(e)}))

    async def onclose(self):
        pass
