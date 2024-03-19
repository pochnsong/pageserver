__all__ = ['SM2Parameter', 'SM2', 'fpow']
from pageserver.utils.base85 import b85decode, b85encode
import random

# SM2椭椭椭圆圆圆曲曲曲线线线公公公钥钥钥密密密码码码算算算法法法推推推荐荐荐曲曲曲线线线参参参数数数
# 推荐使用素数域256位椭圆曲线。
# 椭圆曲线方程：y2 = x3 + ax + b。
# 曲线参数：


class SM2Parameter:
    @staticmethod
    def p():
        return 0xFFFFFFFEFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF00000000FFFFFFFFFFFFFFFF
    @staticmethod
    def a():
        return 0xFFFFFFFEFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF00000000FFFFFFFFFFFFFFFC
    @staticmethod
    def b():
        return 0x28E9FA9E9D9F5E344D5A9E4BCF6509A7F39789F515AB8F92DDBCBD414D940E93

    @staticmethod
    def n():
        return 0xFFFFFFFEFFFFFFFFFFFFFFFFFFFFFFFF7203DF6B21C6052B53BBF40939D54123

    @staticmethod
    def G():
        return 0x32C4AE2C1F1981195F9904466A39C9948FE30BBFF2660BE1715A4589334C74C7, \
            0xBC3736A2F4F6779C59BDCEE36B692153D0A9877CC62A474002DF32E52139F0A0

def fpow(g: int, a: int, q: int):
    e = a % (q - 1)
    if e == 0:
        return 1
    ei = bin(e)
    x = g
    for i in ei[3:]:
        x = x * x % q
        if i == '1':
            x = g * x % q

    return x

def inv(g ,p):
    # p 为质数
    return fpow(g, p-2, p)


def lucas_uv(x: int, y: int, k:int, p: int)->(int, int):
    """
    奇素数p,整数X和Y,正整数k
    """
    k = bin(k)[3:]
    dt = x*x - 4*y
    u = 1
    v = x
    _2_p = inv(2, p)
    for i in k:
        u, v = (u*v) % p, (v*v+dt*u*u) % p * _2_p
        if i == '1':
            u, v = (x*u+v) % p * _2_p, (x*v + dt*u) % p * _2_p

    return u % p, v % p

def mod_sqrt(g: int, p: int) -> int:
    """
    模素数平方根的求解
    y*y = g mod p
    return y
    """
    g = g % p
    error = ValueError("not sqrt value")
    if p % 4 == 3:
        u = (p - 3) >> 2  # p-3/4
        y = fpow(g, u+1, p)
        z = (y * y) % p
        if z == g:
            return y
        raise error

    m = p % 8
    if m == 5:
        u = (p - 5) >> 3  # (p-5)/8
        z = fpow(g, 2*u+1, p)
        if z == 1 % p:
            return fpow(g, u+1, p)
        if z == -1 % p:
            return (((g << 1) % p) * fpow(g << 2, u, p)) % p # g<<1 = g*2 , g<<2=g*4
        raise error

    if m == 1:
        u = (p-1) >> 3  # (p-1)/8
        y = g
        while True:
            x = random.randint(0, p)
            U, V = lucas_uv(x, y, (u << 2)+1, p) # u*4
            if fpow(V, 2, p) == (y << 2) % p: # y*4
                return (V * inv(2, p)) % p
            if U % p not in [1, p-1]:
                raise error

class ECC:
    def __init__(self,  a: int, b: int, p: int):
        if (fpow(a, 3, p)*4+fpow(b, 2, p)*27) % p == 0:
            raise ValueError()
        self.a = a
        self.b = b
        self.p = p

    def check(self, x: int, y: int) -> bool:
        v1 = fpow(x, 3, self.p) + self.a * x + self.b
        v2 = fpow(y, 2, self.p)
        return v1 % self.p == v2

    def y(self, x: int):
        return mod_sqrt(fpow(x, 3, self.p) + self.a*x + self.b, self.p)

    def add(self, x1: int, y1: int, x2: int, y2: int) -> (int, int):
        x3 = x2
        y3 = y2
        if x1 == 0 and y1 == 0:
            return x3, y3

        if x1 == x2:
            # k = (3*x1*x1+self.a)/(2*y1)
            k = (3*x1*x1+self.a)*inv(2*y1, self.p) % self.p
            x3 = (k*k - (x1<<1)) % self.p  # x3 = (k*k - 2*x1) % self.p
            y3 = (k*(x1-x3)-y1) % self.p
        else:
            # k = (y2-y1)/(x2-x1)
            k = (y2 - y1)*inv(x2-x1, self.p)
            x3 = (k*k - x1 - x2) % self.p
            y3 = (k * (x1-x3) - y1) % self.p

        return x3, y3

    def kP(self, x: int, y: int, k: int) -> (int, int):
        bits = bin(k)[2:]
        x2, y2 = 0, 0
        for i in bits:
            x2, y2 = self.add(x2, y2, x2, y2)
            if i == '1':
                x2, y2 = self.add(x2, y2, x, y)
        return x2, y2

def int2bytes(n):
    n = hex(n)[2:]
    l = len(n)
    if l % 2:
        n = '0'+n
        l += 1

    res = [int(n[i: i+2], base=16) for i in range(0, l, 2)]
    return res

def bytes2int(arr):
    res = 0
    for i in range(0, len(arr)):
        res = res << 8 | arr[i]
    return res

class SM2:
    def __init__(self, **kwargs):
        """
        a, b, p, G = (x, y)
        """
        a = int(kwargs.get('a', SM2Parameter.a()))
        b = int(kwargs.get('b', SM2Parameter.b()))
        p = int(kwargs.get('p', SM2Parameter.p()))
        gx, gy = kwargs.get('G', SM2Parameter.G())
        gx = int(gx)
        gy = int(gy)

        self.ecc = ECC(a, b, p)
        self.gx, self.gy = gx, gy
        self._private = None
        self._public = None

        if kwargs.get('auto', True):
            self.init()

    def private_key(self, d=None):
        if d:
            self._private = d
            self._public = self.ecc.kP(self.gx, self.gy, self._private)
        else:
            return self._private

    def init(self):
        if self._private is None:
            self.private_key(self.random_private_key())

    def random_private_key(self) -> int:
        return self.ecc.p - random.randint(1, self.ecc.p >> 2)

    def public_key(self, compress=False):
        x, y = self._public
        if compress:
            res = b85encode([3 if y & 1 else 2] + int2bytes(x))
            return res
        return self._public

    def kP(self, x, y, k):
        return self.ecc.kP(x, y, k)

    def get_point(self, value: str) -> (int, int):
        arr = b85decode(value)
        x = bytes2int(arr[1:])
        y = self.ecc.y(x)
        if (y & 1) ^ (arr[0] & 1):
            y = self.ecc.p - y
        return x, y

    def key_exchange(self, pub_key: str) -> [int]:
        _x, _y = self.get_point(pub_key)
        x, y = self.ecc.kP(_x, _y, self._private)
        x = int2bytes(x)
        y = int2bytes(y)
        res = [0] * 16
        for i in range(16):
            res[i] = (x[i*2] ^ y[i*2]) ^ (x[i*2+1] ^ y[i*2+1])
        return res
