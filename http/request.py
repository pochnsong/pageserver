import urllib.parse
import json
from .query_dict import QueryDict
from .multipart_data import MultipartFormData


def b2s(sss, encode='utf-8'):
    return sss.decode(encode)


def split_path(path):
    if '?' in path:
        return path.split('?', 1)
    return path.rstrip("/"), ''


class Request(object):

    def __init__(self, environ):
        environ = b2s(environ)
        meta = environ.split('\r\n')
        method, path, self.ver = meta[0].split(' ')
        self.method = method.lower()
        self.path, query_string = split_path(path)
        self.GET = QueryDict(urllib.parse.parse_qs(query_string, keep_blank_values=True))
        self.POST = {}
        self.FILES = None
        self.body = None

        self.META = {
            'content-length': 0,
            'connection': '',
        }
        for para in meta[1:]:
            if ':' in para:
                k, v = para.split(':', 1)
                self.META[k.lower()] = v.strip()

    async def setup(self, reader):
        body_len = int(self.META['content-length'])

        if self.method in ['post', 'put', 'delete']:
            content_type = self.META.get('content-type', '').split(';')[0]
            if content_type == 'application/json':
                self.body = await reader.readexactly(body_len) if body_len > 0 else b''
                self.POST = QueryDict(json.loads(self.body))
                return
            if content_type == 'application/x-www-form-urlencoded':
                self.body = await reader.readexactly(body_len) if body_len > 0 else b''
                self.POST = QueryDict(urllib.parse.parse_qs(self.body.decode('utf-8')))
                return
            if content_type == 'multipart/form-data':
                boundary = self.META['content-type'].split(';')[1].split("=")[1].encode('utf-8')
                form = MultipartFormData(reader, body_len=body_len, boundary=boundary)
                await form.setup()
                self.POST = QueryDict(form.data)
                self.FILES = form.files
                return

        self.body = await reader.readexactly(body_len) if body_len > 0 else b''

    @property
    def COOKIE(self):
        if not hasattr(self, '__cookie__'):
            self.__cookie__ = {}
            for kv in self.META['cookie'].split(";"):
                k, v = kv.split("=")
                self.__cookie__[k.strip()] = v

        return self.__cookie__
