from .status import HTTPStatus
import json
from datetime import datetime, date


class HttpResponse(object):
    status_code = 200

    def __init__(self, body="", content_type='text/html;charset=utf-8'):
        self.body = body.encode('utf-8') if isinstance(body, str) else body
        self.now = datetime.utcnow()
        self.header = {}
        self.cookies = {}
        self.content_type = content_type

    def __bytes__(self):
        header = f"HTTP/1.1 {self.status_code} {HTTPStatus[self.status_code]}\r\n"
        header += f"Content-Type: {self.content_type}\r\n"
        header += f"Content-Length: {len(self.body)}\r\n"
        header += "Date: {}\r\n".format(self.now.strftime('%a,%d %b %Y %H:%M:%S GMT'))
        for k, v in self.header.items():
            header += f'{k}: {v}\r\n'

        for k, v in self.cookies.items():
            header += f'Set-Cookie: {k}={v}\r\n'

        return header.encode("utf-8")+b'\r\n'+self.body

    def set_cookie(self, key, value, expires=None, path="/", samesite="Lax", httponly=False,):
        self.cookies[key] = f"{value};Path={path};Same-Site={samesite};{httponly}"

    async def write(self, writer):
        writer.write(bytes(self))
        await writer.drain()


def json_default(val):
    if isinstance(val, date):
        return val.strftime("%Y-%m-%d")
    return val

class JsonResponse(HttpResponse):
    def __init__(self, data):
        super().__init__(json.dumps(data, default=json_default), 'application/json')


class StreamResponse(object):
    status_code = 200

    def __init__(self, stream, content_type="application/octet-stream", headers=None):
        """
        stream 列表或迭代器，返回数据如果不为bytes,会调用str().encode('utf-8')将其变成bytes
        """
        #header += "Content-Disposition: attachment;filename={}\r\n".format(self.filename)
        self.now = datetime.utcnow()
        self.content_type = content_type
        self.length = 0
        self.headers = headers or {}
        self.stream = stream

    def __bytes__(self):
        header = f"HTTP/1.1 {self.status_code} {HTTPStatus[self.status_code]}\r\n"
        header += f"Content-Type: {self.content_type}\r\n"
        header += "Transfer-Encoding: chunked\r\n"
        for k, v in self.headers.items():
            header += f'{k}: {v}\r\n'

        return header.encode("utf-8")+b'\r\n'

    async def write(self, writer):
        writer.write(bytes(self))
        await writer.drain()
        for data in self.stream:
            if not isinstance(data, bytes):
                data = str(data).encode('utf-8')
            writer.write(f"{len(data):x}\r\n".encode("utf-8"))
            writer.write(data+b'\r\n')
            await writer.drain()

        writer.write(b"0\r\n\r\n")
        await writer.drain()


class FileResponse(StreamResponse):
    status_code = 200

    def _stream(self, fd):
        fd.seek(0)
        while True:
            b = fd.read(10240)
            if not b:
                break
            yield b

        fd.close()

    def __init__(self, fd=None, filename="out", content_type="application/octet-stream"):
        super().__init__(
            self._stream(fd), content_type=content_type,
            headers={
                "Content-Disposition": f"attachment;filename={filename}",
            }
        )


class HttpCodeResponse(HttpResponse):
    status_code = 'XXX'

    def __init__(self, msg=None):
        if not msg:
            msg = self.status_code
        super().__init__(f'<h1>{msg}</h1>')


class Http404(HttpCodeResponse):
    status_code = 404


class Http405(HttpCodeResponse):
    status_code = 405


class Http500(HttpCodeResponse):
    status_code = 500


class HttpRedirect(HttpCodeResponse):
    status_code = 302

    def __init__(self, location):
        super().__init__()
        self.header['Location'] = location
