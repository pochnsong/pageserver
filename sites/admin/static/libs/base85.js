/***
 * base85编码
 */
const _b85 = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz!#$%&()*+-;<=>?@^_`{|}~"


function utf8encode(sss) {
    let res = [];
    for (let i = 0; i < sss.length; i++) {
        let c = sss.codePointAt(i);
        if (c <= 0x7f) {
            res.push(c);
            continue
        }
        if (c <= 0x7ff) {
            res.push((192 | (31 & (c >> 6))));
            res.push((128 | (63 & c)))
            continue
        }
        if (c <= 0xffff){
            // Range 3 	U+0800 - U+FFFF 	1110xxxx 10xxxxxx 10xxxxxx
            res.push((224 | (15 & (c >> 12))));
            res.push((128 | (63 & (c >> 6))));
            res.push((128 | (63 & c)))
            continue
        }
        //Range 4 	U+10000 - U+10FFFF 	11110xxx 10xxxxxx 10xxxxxx 10xxxxxx
        res.push((240 | (7 & (c >> 18))));
        res.push((128 | (63 & (c >> 12))));
        res.push((128 | (63 & (c >> 6))));
        res.push((128 | (63 & c)))
        i ++
    }
    return res
}

function utf8decode(arr) {
    let res = "";
    for (let i = 0; i < arr.length;i++) {
        let v = arr[i];
        let c = v;
        if(v>239){ //0b11110000 = 240
            //Range 4 	U+10000 - U+10FFFF 	11110xxx 10xxxxxx 10xxxxxx 10xxxxxx
            c = (v & 7) << 18 
            c |= (arr[i+1] & 63) << 12
            c |= (arr[i+2] & 63) << 6
            c |=  arr[i+3] & 63
            i += 3
        }else if (v > 223) {//0b11100000 = 224
            c = (v & 15) << 12
            c |= (arr[i+1] & 63) << 6
            c |=  arr[i+2] & 63
            i += 2
        } else if (v > 191) { // 0b11000000 = 192
            c = (v & 0b00011111) << 6
            c |= arr[i+1] & 63
            i += 1
        }
        res += String.fromCodePoint(c)
    }
    return res
}
function b85encode(arr){
    let l = 4 - arr.length % 4
    for(let i=0;i<l; i++){
        arr.push(l)
    }

    let res = []
    for(let i=0;i<arr.length;i+=4){
        let c = arr[i] << 24 | arr[i+1] << 16 | arr[i+2] << 8 | arr[i+3]
        c = c >>> 0
        let v = (c / 52200625 |0 ) % 85
        res.push(_b85.charAt(v))
        v = (c / 614125 | 0) % 85
        res.push(_b85.charAt(v))
        v = (c / 7225 | 0) % 85
        res.push(_b85.charAt(v))
        v = (c / 85 | 0) % 85
        res.push(_b85.charAt(v))
        v = c % 85
        res.push(_b85.charAt(v))
    }
    return res.join("");
}
function b85decode(sss){
    let res = []
    let ord = {}
    for(let i =0;i<_b85.length;i++){
        ord[_b85[i]] = i
    }        


    for(let i=0;i<sss.length;i+=5){
        let c = 0
        c  = ord[sss.charAt(i  )] * 52200625 // 85**4
        c += ord[sss.charAt(i+1)] * 614125 //85**3
        c += ord[sss.charAt(i+2)] * 7225 // 85**2
        c += ord[sss.charAt(i+3)] * 85
        c += ord[sss.charAt(i+4)]
        let tmp = [c & 0xff]
        c >>= 8
        tmp.unshift(c & 0xff)
        c >>= 8
        tmp.unshift(c & 0xff)
        c >>= 8
        tmp.unshift(c & 0xff)
        res = res.concat(tmp)
    }
    return res.slice(0, -res[res.length-1])
}

function a85encode(arr){
    let l = 4 - arr.length % 4
    for(let i=0;i<l; i++){
        arr.push(l)
    }
    let res = []
    for(let i=0;i<arr.length;i+=4){
        let c = arr[i] << 24 | arr[i+1] << 16 | arr[i+2] << 8 | arr[i+3]
        c = c >>> 0
        let v = (c / 52200625 |0 ) % 85 + 33
        res.push(String.fromCharCode(v))
        v = (c / 614125 | 0) % 85 + 33
        res.push(String.fromCharCode(v))
        v = (c / 7225 | 0) % 85 + 33
        res.push(String.fromCharCode(v))
        v = (c / 85 | 0) % 85 + 33
        res.push(String.fromCharCode(v))
        v = c % 85 + 33
        res.push(String.fromCharCode(v))
    }
    return res.join("");
}
function a85decode(sss){
    let res = []
    
    for(let i=0;i<sss.length;i+=5){
        let c = 0
        c  = (sss.charCodeAt(i  ) - 33) * 52200625 // 85**4
        c += (sss.charCodeAt(i+1) - 33) * 614125 //85**3
        c += (sss.charCodeAt(i+2) - 33) * 7225 // 85**2
        c += (sss.charCodeAt(i+3) - 33) * 85
        c +=  sss.charCodeAt(i+4) - 33
        let tmp = [c & 0xff]
        c >>= 8
        tmp.unshift(c & 0xff)
        c >>= 8
        tmp.unshift(c & 0xff)
        c >>= 8
        tmp.unshift(c & 0xff)
        res = res.concat(tmp)
    }
    return res.slice(0, -res[res.length-1])
}
function bytes(sss){
    let res = []
    for(let i=0;i<sss.length;i++){
        res.push(sss.charCodeAt(i))
    }
    return res
}
function makePassword(pwd, min_lenght=16){
    if(pwd.length==0){
        return ''
    }
    pwd = utf8encode(pwd)
    while(true){
        pwd = b85encode(pwd)
        if(pwd.length>min_lenght){
            break
        }
        pwd = bytes(pwd)
    }
    return pwd
}

export {
    a85encode, a85decode,
    b85encode, b85decode, 
    utf8encode, utf8decode, 
    makePassword,
}