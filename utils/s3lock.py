class S3Lock:
    def __init__(self, key):
        self.key = key
        if isinstance(key, str):
            self.key = [ord(k) for k in key]

    def encrypt(self, content, with_hex=False):
        if not isinstance(content, bytes):
            raise Exception("required bytes")

        i = 0
        res = bytearray(len(content))
        block = bytearray(content)
        while block:
            for k in self.key:
                if not block:
                    break

                pos = k % len(block)
                if pos == len(block):
                    pos = 0

                x = block.pop(pos)
                res[i] = x ^ (k & 255)
                i += 1

        if with_hex:
            return bytes.hex(bytes(res))
        return bytes(res)

    def decrypt(self, content, with_hex=False):
        if with_hex:
            content = bytes.fromhex(content)

        if not isinstance(content, bytes):
            raise Exception("required bytes")

        i = 0
        length = len(content)
        res = bytearray(length)
        pos = list(range(length))

        while i < length:
            for k in self.key:
                if i == length:
                    break

                p = k % len(pos)
                if p == len(pos):
                    p = 0

                j = pos.pop(p)
                res[j] = content[i] ^ (k & 255)
                i += 1

        return bytes(res)
