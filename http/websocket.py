import struct
import base64
import hashlib
from enum import IntEnum

__all__ = [
    'WebSocket',
    'OPCODE',
]

MAGIC_STRING = '258EAFA5-E914-47DA-95CA-C5AB0DC85B11'


class OPCODE(IntEnum):
    EXTRA = 0x0
    TEXT = 0x1
    BYTES = 0x2
    CLOSE = 0x8
    PING = 0x9
    PONG = 0xA


class WebSocketCloseException(Exception):
    pass


class WebSocket(object):

    @staticmethod
    async def handshake(request, writer):
        key = request.META['sec-websocket-key'] + MAGIC_STRING
        sec_accept = base64.b64encode(hashlib.sha1(key.encode('utf-8')).digest())

        response = (
            f"HTTP/1.1 101 Switching Protocols\r\n"
            f"Upgrade:websocket\r\n" 
            f"Connection: Upgrade\r\n" 
            f"Sec-WebSocket-Accept: {sec_accept.decode('utf-8')}\r\n" 
            f"WebSocket-Location: ws://{request.META['host']}{request.path}\r\n\r\n"
        ).encode('utf-8')
        writer.write(response)
        await writer.drain()

    @staticmethod
    async def receive(reader):
        data = await reader.readexactly(2)

        flag_fin = data[0] & 0b10000000
        flag_opcode = data[0] & 0b00001111
        flag_mask = data[1] & 0b10000000
        payload_len = data[1] & 0b01111111

        if flag_opcode == OPCODE.CLOSE:
            raise WebSocketCloseException()

        if payload_len == 126:
            msg_len = await reader.readexactly(2)
            msg_len = struct.unpack('>H', msg_len)[0]
            data = await reader.readexactly(4+msg_len)
            mask = data[:4]
            _msg = data[4:]

        elif payload_len == 127:
            msg_len = await reader.readexactly(8)
            msg_len = struct.unpack('>Q', msg_len)[0]
            data = await reader.readexactly(4+msg_len)
            mask = data[:4]
            _msg = data[4:]
        else:
            msg_len = payload_len
            data = await reader.readexactly(4+msg_len)
            mask = data[:4]
            _msg = data[4:]
        msg = bytearray()
        for i in range(len(_msg)):
            chunk = _msg[i] ^ mask[i % 4]
            msg.append(chunk)

        if flag_opcode == OPCODE.PING:
            return {
                'type': 'ping',
                'text': None,
                'bytes': bytes(msg)
            }

        if flag_opcode == OPCODE.TEXT:
            return {
                'type': 'websocket',
                'text': msg.decode('utf-8'),
                'bytes': None}

        return {
            'type': 'websocket',
            'text': None,
            'bytes': bytes(msg)}

    @staticmethod
    async def send(writer, flag_opcode, msg=''):
        if isinstance(msg, str):
            msg = msg.encode('utf-8')

        msg_len = len(msg)
        if msg_len > 2**64:
            raise Exception('暂不支持超大数据')

        data = struct.pack('>B', flag_opcode | 0b10000000)
        if msg_len > 65535:
            payload_len = struct.pack('>b', 127)
            payload_len += struct.pack('>Q', msg_len)
        elif msg_len > 125:
            payload_len = struct.pack('>b', 126)
            payload_len += struct.pack('>H', msg_len)
        else:
            payload_len = struct.pack('>b', msg_len)

        data += payload_len
        data += msg
        writer.write(data)
        await writer.drain()

    @staticmethod
    async def disconnect(writer):
        writer.close()
        await writer.wait_closed()

    @classmethod
    async def close(cls, writer):
        try:
            await cls.send(writer, OPCODE.CLOSE)
            await cls.disconnect(writer)
        except ConnectionResetError:
            pass
