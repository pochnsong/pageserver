def utf8encode(sss):
    res = []
    for s in sss:
        c = ord(s)
        if c <= 0x7f:
            res.append(c)
            continue
        if c <= 0x7ff:
            res += [192 | 31 & c >> 6, 128 | 63 & c]
            continue
        if c <= 0xffff:
            res += [224 | 15 & c >> 12, 128 | 63 & c >> 6, 128 | 63 & c]
            continue

        res += [240 | 7 & c >> 18, 128 | 63 & c >> 12, 128 | 63 & c >> 6, 128 | 63 & c]
    return res

def utf8decode(arr):
    res = ""
    i = 0
    l = len(arr)
    while i < l:
        v = arr[i]
        c = v
        if v > 239:  # 0b11110000 = 240
            c = (v & 7) << 18
            c |= (arr[i+1] & 63) << 12
            c |= (arr[i+2] & 63) << 6
            c |= arr[i+3] & 63
            i += 3
        elif v > 223:  # 0b11100000 = 224
            c = (v & 15) << 12
            c |= (arr[i+1] & 63) << 6
            c |= arr[i+2] & 63
            i += 2
        elif v > 191:  # 0b11000000 = 192
            c = (v & 0b00011111) << 6
            c |= arr[i+1] & 63
            i += 1
        res += chr(c)
        i += 1
    return res


def bytes2hex(ll):
    res = ""
    for x in ll:
        res += hex(x)[2:].rjust(2, '0')
    return res


def hex2bytes(ss):
    res = []
    for i in range(0, len(ss), 2):
        res.append(int(ss[i: i+2], 16))
    return res


def bytes2str(ll):
    res = ""
    for x in ll:
        res += chr(x)
    return res