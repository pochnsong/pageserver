const VERSION = "1.0"

export default class JSONX {
    constructor(data) {
        this.data = data
        this.i = 0
        this.length = data.length
    }
    char(){
        return this.data.charAt(this.i)
    }
    getStr() {
        let res = ""
        for (this.i++; this.i < this.length; this.i++) {
            let c = this.char()
            if (c == "\\") {
                this.i++
                res += c
                res += this.char()
                continue
            }
            if (c == '"') { 
                this.i++
                break 
            }
            res += c
        }
        return JSON.parse(`{"_":"${res}"}`)._
    }
    readUntil(c) {
        for (; this.i < this.length; this.i++) {
            if (this.char() == c) {
                this.i++
                break
            }
        }
    }
    readEmpty() {
        for (; this.i < this.length; this.i++) {
            let c = this.char()
            if (c == '\x20' || c == '\x0a' || c == '\x0d' || c=='\x09') {
                continue
            } else {
                break
            }
        }
    }
    getAttr() {
        this.readUntil('"')
        this.i --
        let v = this.getStr()
        this.readUntil(":")
        return v
    }
    getVal() {
        this.readEmpty()
        let val = ""
        let c = this.char()
        let format = true
        if (c == '[') {
            val = this.getList()
            format = false
        }else if (c == '{') {
            val = this.getObject()
            format = false
        }else if (c == '"') {
            val = this.getStr()
            format = false
        }
        for (; this.i < this.length; this.i++) {
            c = this.char()            
            if (c == ',') {
                this.i++
                break
            }
            if (c == ']') { break }
            if (c == '}') { break }
            val += c
        }
        if(format){
            let re = /\d{15,}/
            val = val.trim()
            if(re.test(val)){
                val = `"${val}"`
            }
            val = JSON.parse(`{"_":${val}}`)._    
        }
        return val
    }
    getList() {
        let res = []
        for (this.i += 1; this.i < this.length;) {
            let c = this.char()
            if (c == ']') {
                this.i++
                break
            }
            let v = this.getVal()
            res.push(v)
        }
        return res
    }
    getObject() {
        let res = {}
        let attr = ''
        for (this.i += 1; this.i < this.length;) {
            if (this.char() == '}') {
                this.i++
                break
            }
            attr = this.getAttr()
            res[attr] = this.getVal()
        }
        return res
    }
    parse(){
        this.readEmpty()
        if(this.char()=='{'){
            return this.getObject()
        }
        if(this.char() == "["){
            return this.getList()
        }
        return this.data
    }
}
export { JSONX }

