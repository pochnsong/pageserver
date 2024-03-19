"""
精确的带pad的base85编码
"""
__all__ = ["b85encode", "b85decode", "a85encode", "a85decode"]

_x85 = ("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        "abcdefghijklmnopqrstuvwxyz!#$%&()*+-;<=>?@^_`{|}~")




def b85encode(arr: list[int]):
    l = 4 - len(arr) % 4
    arr = arr + [l]*l

    res = ""

    for i in range(0, len(arr), 4):
        c = arr[i] << 24 | arr[i+1] << 16 | arr[i+2] << 8 | arr[i+3]
        v = (c // 52200625) % 85
        res += _x85[v]
        v = (c // 614125) % 85
        res += _x85[v]
        v = (c // 7225) % 85
        res += _x85[v]
        v = (c // 85) % 85
        res += _x85[v]
        v = c % 85
        res += _x85[v]

    return res


def b85decode(sss: str) -> list[int]:
    res = []
    _ord = {}
    for i, c in enumerate(_x85):
        _ord[c] = i

    for i in range(0, len(sss), 5):
        c = _ord[sss[i]] * 52200625   # 85 ** 4
        c += _ord[sss[i+1]] * 614125  # 85 ** 3
        c += _ord[sss[i+2]] * 7225    # 85 ** 2
        c += _ord[sss[i+3]] * 85
        c += _ord[sss[i+4]]
        res += [c >> 24 & 0xff, c >> 16 & 0xff, c >> 8 & 0xff, c & 0xff]

    return res[:-res[-1]]


def a85encode(arr: list[int]):
    l = 4 - len(arr) % 4
    arr = arr + [l]*l

    res = ""

    for i in range(0, len(arr), 4):
        c = arr[i] << 24 | arr[i+1] << 16 | arr[i+2] << 8 | arr[i+3]
        v = (c // 52200625) % 85 + 33
        res += chr(v)
        v = (c // 614125) % 85 + 33
        res += chr(v)
        v = (c // 7225) % 85 + 33
        res += chr(v)
        v = (c // 85) % 85 + 33
        res += chr(v)
        v = c % 85 + 33
        res += chr(v)

    return res


def a85decode(sss: str) -> list[int]:
    res = []

    for i in range(0, len(sss), 5):
        c = (ord(sss[i]) - 33) * 52200625   # 85 ** 4
        c += (ord(sss[i+1]) - 33) * 614125  # 85 ** 3
        c += (ord(sss[i+2]) - 33) * 7225    # 85 ** 2
        c += (ord(sss[i+3]) - 33) * 85
        c += ord(sss[i+4]) - 33
        res += [c >> 24 & 0xff, c >> 16 & 0xff, c >> 8 & 0xff, c & 0xff]

    return res[:-res[-1]]
