import {b85decode, b85encode} from './base85.js'


const ECC_p = '0xFFFFFFFEFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF00000000FFFFFFFFFFFFFFFF'
const ECC_a = '0xFFFFFFFEFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF00000000FFFFFFFFFFFFFFFC'
const ECC_b = '0x28E9FA9E9D9F5E344D5A9E4BCF6509A7F39789F515AB8F92DDBCBD414D940E93'
const ECC_n = '0xFFFFFFFEFFFFFFFFFFFFFFFFFFFFFFFF7203DF6B21C6052B53BBF40939D54123'
const ECC_Gx = '0x32C4AE2C1F1981195F9904466A39C9948FE30BBFF2660BE1715A4589334C74C7'
const ECC_Gy = '0xBC3736A2F4F6779C59BDCEE36B692153D0A9877CC62A474002DF32E52139F0A0'


function mod(x, p){
    let res = x % p
    return res<0 ? res + p : res
}
function fpow(g, a, q){
    //g = BigInt(g)
    //a = BigInt(a)
    //q = BigInt(q)
    let e = mod(a , q - 1n)

    if(e == 0n){return 1n}
    let ei = e.toString(2)
    let x = g
    for(let i = 1;i<ei.length;i++){
        x = mod(x * x , q)
        if(ei[i] == '1')
            x = mod(g * x , q)
    }
    return x
}

function inv(g ,p){
    // p 为质数
    //g = BigInt(g)
    //p = BigInt(p)
    return fpow(g, p-2n, p)
}

function lucas_uv(x, y, k, p){
    
    //奇素数p,整数X和Y,正整数k
    
    k = k.toString(2)
    let dt = x*x - 4n*y
    let u = 1n
    let v = x
    let _2_p = inv(2n, p)

    for(let i=1;i<k.length;i++){

        [u, v] = [mod(u*v, p), mod(v*v+dt*u*u, p) * _2_p]

        if(k[i] == '1'){
            [u, v] = [mod(x*u+v, p) * _2_p, mod(x*v + dt*u, p) *_2_p]
        }

    }
    return [mod(u,p) , mod(v,p)]
}
function rshifts(x, n){
    //大数x右移n
    return BigInt('0b'+x.toString(2).slice(0, -n))
}
function lshifts(x, n){
    //大数x左移n
    return BigInt('0b'+x.toString(2)+Array(n+1).join(0))
}
function random(max_value){
    let m = max_value.toString()
    let res = ''
    for(let i=1;i<m.length;i++){
        res += (Math.random()*10)|0
    }
    return max_value - BigInt(res) - 1n
}

function mod_sqrt(g, p){
    /*
    模素数平方根的求解
    y*y = g mod p
    return y
    */
   let _g = g
    g = mod(g , p)
    let error = "not sqrt value"

    if(mod(p , 4n) == 3n){
        let u = rshifts(p - 3n, 2)  // (p-3)/4
        let y = fpow(g, u+1n, p)
        let z = mod(y * y , p)
        if(z == g){
            return y
        }
        throw error
    }
    let m = mod(p , 8n)
    if(m == 5){
        let u = rshifts(p - 5n, 3)  // (p-5)/8
        let z = fpow(g, 2n*u+1n, p)
        if(z == mod(1n , p)){
            return fpow(g, u+1n, p)
        }
        if(z == mod(-1n , p)){
            return mod(mod(lshifts(g, 1) , p) * fpow(lshifts(g , 2), u, p) , p) // g<<1 = g*2 , g<<2=g*4
        }
        throw error
    }
    if(m == 1n){
        let u = rshifts(p-1n, 3)  // (p-1)/8
        let y = g
        while (true){
            let x = random(p-1n)
            let [U, V] = lucas_uv(x, y, lshifts(u , 2)+1n, p) // u*4
            if(fpow(V, 2n, p) == mod(lshifts(y , 2) , p)){ // y*4
                return mod(V * inv(2n, p), p)
            }
            let U_p = mod(U , p)
            if( U_p != 1n && U_p != p-1n){
                throw error
            }
        }
    }
}

function int2bytes(n){
    n = n.toString(16)
    let l = n.length
    if(l % 2){
        n = '0'+n
        l += 1
    }
    let res = []

    for(let i =0;i<l;i+=2){
        res.push(Number('0x'+n.slice(i, i+2)))
    }
    return res
}

function bytes2int(arr){
    let res = '0x'
    arr.forEach(o => {
        res += o.toString(16).padStart(2,'0')
    });
    return BigInt(res)
}

class ECC{
    constructor(a, b, p) {
        a = BigInt(a)
        b = BigInt(b)
        p = BigInt(p)
        if( (a*a*a*4n+b*b*27n) % p == 0n){
            throw "error"
        }
        this.a = a
        this.b = b
        this.p = p
        this.gx = null
        this.gy = null
    }
    add(x1, y1, x2, y2){

        let x3 = x2
        let y3 = y2
        if(x1 == 0n && y1 == 0n){
            return [x3, y3]
        }

        if(x1 == x2){
            // k = (3*x1*x1+self.a)/(2*y1)
            let k = mod((3n*x1*x1+this.a)*inv(2n*y1, this.p) , this.p)
            x3 = mod(k*k - 2n*x1 , this.p)
            y3 = mod(k*(x1-x3)-y1, this.p)
        }else{
            // k = (y2-y1)/(x2-x1)
            let k = (y2 - y1)*inv(x2-x1, this.p)
            x3 = mod(k*k - x1 - x2 , this.p)
            y3 = mod(k * (x1-x3) - y1, this.p)
        }
        return [x3, y3]
    }
    kP(x, y, k){
        //x = BigInt(x)
        //y = BigInt(y)
        //k = BigInt(k)

        let bits = k.toString(2)
        let x2 = 0n, y2  = 0n
        for(let i=0;i<bits.length;i++){
            let v = this.add(x2, y2, x2, y2)
            x2 = v[0] 
            y2 = v[1]
            if(bits[i] == '1'){
                v = this.add(x2, y2, x, y)
                x2 = v[0] 
                y2 = v[1]    
            }
        };
        return [x2, y2]
    }
    y(x){
       return mod_sqrt(fpow(x, 3n, this.p) + this.a*x + this.b, this.p) 
    }
}

class SM2{
    constructor(params){
        let a, b, p, n, gx, gy
        if (params){
            a = BigInt(params.a)
            b = BigInt(params.b)
            p = BigInt(params.p)
            n = BigInt(params.n)
            gx = BigInt(gx)
            gy = BigInt(gy)
        }else{
            a = BigInt(ECC_a)
            b = BigInt(ECC_b)
            p = BigInt(ECC_p)
            gx = BigInt(ECC_Gx)
            gy = BigInt(ECC_Gy)
            n = BigInt(ECC_n)
        }
        this.n = n
        this.ecc = new ECC(a, b, p)
        this.gx = gx
        this.gy = gy
        this._private = null
        this._public = null
        this.key = null
        this.setPrivateKey(random(this.n))
    }
    getPrivateKey(){
        return this._private.toString(16)
    }
    setPrivateKey(key){
        this._private = BigInt('0x'+key)
        this._public = this.ecc.kP(this.gx, this.gy, this._private)
    }
    getPoint(value){
        let arr = b85decode(value)
        let x = bytes2int(arr.slice(1))
        let y = this.ecc.y(x)
        if( (y & 1n) ^ BigInt(arr[0] & 1)){
            y = this.ecc.p - y
        }
        return [x, y]
    }
    getPublicKey(){
        let [x, y] = this._public
        let dat = int2bytes(x)
        dat.unshift( y & 1n? 3: 2)
        return b85encode(dat)
    }
    getKeyExchange(pub_key){
        let [_x, _y] = this.getPoint(pub_key)
        let [x, y] = this.ecc.kP(_x, _y, this._private)
        x = int2bytes(x)
        y = int2bytes(y)
        let res = new Array(16)
        for(let i=0;i<16; i++){
            res[i] = (x[i*2] ^ y[i*2]) ^ (x[i*2+1] ^ y[i*2+1])
        }
        return res
    }

}
export {
    ECC, SM2, bytes2int, int2bytes
}