from pageserver.utils.gmsm.sm2 import SM2
from pageserver.utils.gmsm.sm4 import SM4
from pageserver.utils.base85 import a85decode, a85encode
from pageserver.utils.byteslib import utf8encode, utf8decode, hex2bytes
from .settings import SECRET_KEY_SM4, SECRET_KEY_SM2
Secrets = SM2(auto=False)
Secrets.private_key(SECRET_KEY_SM2)


def encrypt(msg, key):
    if isinstance(key, str):
        key = hex2bytes(key)
    sm4 = SM4(key)
    if isinstance(msg, bytes):
        msg = list(bytearray(msg))
    else:
        msg = utf8encode(msg)
    msg = sm4.encrypt(msg)
    msg = a85encode(msg)
    return msg

def decrypt(msg, key):
    if isinstance(key, str):
        key = hex2bytes(key)
    sm4 = SM4(key)
    msg = a85decode(msg)
    msg = sm4.decrypt(msg)
    msg = utf8decode(msg)
    return msg
