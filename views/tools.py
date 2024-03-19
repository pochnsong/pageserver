from pageserver.views.generic import *
from pageserver.http.response import JsonResponse
from pageserver.cache import cache
from pageserver.conf import settings
import asyncio
from functools import partial
import os
import shutil
import time


class UploadBlockAPI(API):

    def check_perm(self):
        return False

    @classmethod
    def temp_path(cls, cache_key):
        return os.path.join(settings.TEMP_DIR, cache_key)

    def get_cache_key(self):
        return f"file-{time.time()}"

    @classmethod
    def _save_file(cls, cache_key, save_as, auto_remove=True):

        save_dir = os.path.dirname(save_as)
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

        temp_file = os.path.join(settings.TEMP_DIR, cache_key)
        if auto_remove:
            shutil.move(temp_file, save_as)
        else:
            shutil.copy(temp_file, save_as)

    @classmethod
    async def save_file(cls, cache_key, save_as, auto_remove=True):
        if not cache_key:
            return None
        loop = asyncio.get_running_loop()
        fn = partial(cls._save_file, cache_key, save_as, auto_remove)
        await loop.run_in_executor(None, fn)

    @classmethod
    def save_chunk(cls, cache_key, chunk, i=0):
        save_as = os.path.join(settings.TEMP_DIR, cache_key)
        if not os.path.exists(settings.TEMP_DIR):
            os.makedirs(settings.TEMP_DIR)

        if i == 0:
            with open(save_as, 'wb') as wf:
                wf.write(chunk)
            return

        with open(save_as, 'ab') as wf:
            wf.write(chunk)

    async def post(self, request):
        total = int(request.POST['total'])
        i = int(request.POST['i'])
        chunk = request.FILES['chunk'][0].read()

        cache_key = self.get_cache_key()

        loop = asyncio.get_running_loop()
        save_fn = partial(self.save_chunk, cache_key, chunk, i)
        await loop.run_in_executor(None, save_fn)

        if i == total-1:
            return JsonResponse({'status': 'OK', 'file_key': cache_key})

        return JsonResponse({'status': 'OK', 'i': i})

