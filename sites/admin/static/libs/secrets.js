import {utf8encode, utf8decode, a85decode, a85encode} from "./base85.js"
import {SM2} from "./sm2.js"
import {SM4} from "./sm4.js"

let sm4 = null
function getKeyExchange(pubkey){
    let sm2 = new SM2()
    let key = sm2.getKeyExchange(pubkey)
    return [sm2.getPublicKey(), key]
}
function setKey(key){
    sm4 = key? new SM4(key): null
}
function encrypt(msg){
    if(typeof msg == 'object'){
        msg = JSON.stringify(msg)
    }
    return a85encode(sm4.encrypt(utf8encode(msg)))
}

function decrypt(msg){
    msg = a85decode(msg)
    msg = sm4.decrypt(msg)
    msg = utf8decode(msg)
    return msg
}

export {encrypt, decrypt, getKeyExchange, setKey}
