import tempfile

def b2s(sss):
    return sss.decode('utf-8')

class MultipartFormData:

    def __init__(self, reader, body_len, boundary):
        self.reader = reader
        self.body_len = body_len
        self.boundary = b'--'+boundary
        self.buffer_size = len(boundary)*10  # 缓存大小不能小于boundary大小

        self.buffer = b''
        self.data = {}
        self.files = {}

    def __del__(self):
        self.reader = None
        self.data = None
        self.files = None

    async def _read(self):
        read_size = min(self.body_len, self.buffer_size)
        self.body_len -= read_size
        return await self.reader.readexactly(read_size)

    async def read(self):
        if not self.body_len:
            return self.buffer

        return self.buffer + await self._read()

    async def readuntil(self, flag):
        while True:
            chunks = self.buffer.split(flag, 1)
            if len(chunks) > 1:
                self.buffer = chunks[1]
                return chunks[0]+flag

            if not self.body_len:
                return self.buffer

            self.buffer += await self._read()

    async def process_header(self):
        header_raw = await self.readuntil(b'\r\n\r\n')
        if header_raw == b'--\r\n':
            return None

        headers = b2s(header_raw).strip('\r\n').split('\r\n')

        info = {
            'type': "value"
        }
        for kv in headers[0].split(";")[1:]:
            k, v = kv.split("=")
            info[k.strip()] = v.strip('"')

        if 'filename' in info:
            info["type"] = "file"

        return info

    async def process_value(self):
        value_raw = await self.readuntil(self.boundary)
        value = b2s(value_raw.split(b'\r\n'+self.boundary)[0])
        return value

    async def process_file(self, info):
        name = info['name']
        tf = tempfile.TemporaryFile()
        setattr(tf, "filename", info['filename'])
        boundary_len = len(self.boundary)
        while True:

            raw = await self.read()
            if not raw:
                break

            chunks = raw.split(b'\r\n'+self.boundary, 1)
            if len(chunks) == 2:  # 找到
                tf.write(chunks[0])
                self.buffer = chunks[1]
                break
            else:
                tf.write(raw[:-boundary_len])
                self.buffer = raw[-boundary_len:]

            if not self.body_len:
                break

        tf.seek(0)
        if name not in self.files:
            self.files[name] = []
        self.files[name].append(tf)

    async def setup(self):
        await self.readuntil(self.boundary+b'\r\n')
        while True:
            header = await self.process_header()
            if header is None:
                break
            if header['type'] == 'value':
                self.data[header['name']] = await self.process_value()
            if header['type'] == 'file':
                self.data[header['name']] = header['filename']
                await self.process_file(header)
