"""
"""
from pageserver.utils.byteslib import *
from pageserver.utils.gmsm.sm4 import SM4
from pageserver.utils.time import get_timestamp
import time
import hashlib
import json
import base64
import hmac

from random import SystemRandom
_sysrand = SystemRandom()

_TIMESTAMP_BASE = 2020
def get_random_string(length=12,
                      allowed_chars='abcdefghijklmnopqrstuvwxyz'
                                    'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'):
    """
    Return a securely generated random string.

    The default length of 12 with the a-z, A-Z, 0-9 character set returns
    a 71-bit value. log_2((26+26+10)^12) =~ 71 bits
    """
    return ''.join(_sysrand.choice(allowed_chars) for i in range(length))


def create_session_id():
    res = f"{time.time_ns()}{get_random_string(32)}"
    return res


def create_token(value, secret_key, expire=60*60*24*7, create_time=None):
    """
    :param value: str 加密消息
    :param secret_key: str 密钥
    :param expire: 过期时间，秒
    :param create_time 创建时间
    :return: sha1(40)+base64(expire_time(10)+message)
    """
    if create_time is None:
        create_time = time.time()
    message = f"{create_time}-{expire}-{value}"
    b64_message = base64.urlsafe_b64encode(message.encode('utf-8'))
    _token = hmac.new(secret_key.encode('utf-8'), b64_message, 'sha1').hexdigest()
    token = f"{_token}{b64_message.decode('utf-8')}"
    return token


def check_token(token, key):
    """
    token 格式
    :param key:
    :param token:
    :return:
    """
    if not token:
        return False

    _token, b64_message = token[:40], token[40:]

    sha1 = hmac.new(key.encode("utf-8"), b64_message.encode('utf-8'), 'sha1').hexdigest()
    if sha1 != _token:
        return False

    message = base64.urlsafe_b64decode(b64_message).decode('utf-8').split('-', 2)
    create_time = float(message[0])
    expire_time = create_time+float(message[1])
    if expire_time < time.time():
        return False

    return message[2]


def create_cipher_token(value, sm4, expire=60 * 60 * 24 * 7, create_time=None):
    if create_time is None:
        create_time = get_timestamp(base=_TIMESTAMP_BASE)

    msg = {
        '_': value,
        'ex': expire,
        'ct': create_time,
    }

    msg = utf8encode(json.dumps(msg))
    msg = sm4.encrypt(msg)
    return base64.urlsafe_b64encode(bytearray(msg)).decode('utf-8')


def check_cipher_token(token, sm4):
    """
    token 格式
    :param token:
    :return:
    """
    if not token:
        return None

    try:
        msg = json.loads(utf8decode(sm4.decrypt(list(base64.urlsafe_b64decode(token)))))
        expire_time = msg['ct']+msg['ex']
        if expire_time > get_timestamp(base=_TIMESTAMP_BASE):
            return msg['_']
    except:
        pass

    return None


def make_password(password, salt=None, iterations=150000):
    if not salt:
        salt = get_random_string()
    _hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), iterations)
    _hash = base64.b64encode(_hash).decode('ascii').strip()
    return "%s$%d$%s$%s" % ("pbkdf2_sha256", iterations, salt, _hash)


def check_password(password, encoded):
    algorithm, iterations, salt, _hash = encoded.split('$', 3)
    encoded_2 = make_password(password, salt, int(iterations))
    return hmac.compare_digest(encoded.encode('utf-8'), encoded_2.encode('utf-8'))



