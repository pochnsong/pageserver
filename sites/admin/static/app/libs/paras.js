import { encrypt, decrypt } from "../../libs/secrets.js";
import JSONX from "../../libs/jsonx.js"

class Http{
   static async request(method, url, query='', data=null, headers={}) {
      headers = Object.assign({'If-Modified-Since': '0'}, headers)
      if(data && `${data}` == "[object Object]"){
         headers['content-type'] = 'application/json';
      }

      let login = System.login.get();
      if (login) {
         if(login.key){
            headers[login.key] = login.token;
         }
      }

      if(login && login.sm4){
         if(data && `${data}` == "[object Object]"){
            data = JSON.stringify(data)
            data = encrypt(data)
            headers['content-type'] = 'text/sm4';
         }

         if(query && `${query}` == "[object Object]"){
            query = JSON.stringify(query)
            query = `q=${encodeURIComponent(encrypt(query))}`
         }
      }


      return new Promise(function (resolve, reject) {
         let xhr = new XMLHttpRequest();
         if(query){query = `?${query}`}
         xhr.open(method, `${System.host.get()}${url}${query}`, true);
         Object.entries(headers).forEach(function(kv){
            xhr.setRequestHeader(kv[0], kv[1]);
         })
         xhr.onload = function () {
             if (this.status == 200 | xhr.status == 304) {
               /**
                * data = data.replace(/:\s*(\d{15,})/g, ': "$1"');
               data = data.replace(/\[\s*(\d{15,})/g, '\["$1"');
               data = data.replace(/,\s*(\d{15,})/g, ', "$1"');
                */
               let res = this.response
               if(this.getResponseHeader('content-type') == 'text/sm4'){
                  res = decrypt(res)
                  let jsonx = new JSONX(res)
                  res = jsonx.parse()
               }
               else if(this.getResponseHeader('content-type') == 'application/json'){
                  res = JSON.parse(res)
               }
               resolve(res);
             } else if (this.status == 404) {
                 resolve("");
             }
             else {
                 resolve({status: 'FAIL', errors: this.response});
             }
         }
         xhr.send(data);
     })
   }
   static async upload(url, blob, name, process, i = 0) {
      /** 
       * fileinfo:{
       * path,
       * name,
       * size,
       * }
      */
      return new Promise(async (resolve, reject) => {
         let size = blob.size;
         const chunk_size = 102400;
         let total = Math.ceil(parseFloat(size) / chunk_size);
         //let i = 0;
         let res = null;
         let retry = 0;
         while (i < total) {
            try {
               let form = new FormData();
               form.append("i", i);
               form.append("total", total);
               form.append("name", name);
               form.append("chunk", blob.slice(i * chunk_size, (i + 1) * chunk_size));

               res = await Http.request('post', url, '', form);
               if (res.status == 'OK') {
                  process && process({ total: total, i: i + 1 });
                  i += 1;
               } else {
                  throw (res)
               }

            } catch (e) {
               retry += 1;
               if (retry > 10) {
                  resolve({ 'status': 'FAIL', 'errors': e, 'i': i })
                  return
               }
            }
         }
         resolve(res)
      })
   }
   static async post(url, data, callback){
      let res = await Http.request('post', url, '', data)
      if(callback){
         callback(res)
      }else{
         return res
      }      
   }
   static async get(url, query, callback){
      if(typeof query == 'function'){
         callback = arguments[1];
         query = '';   
      }

      let res = await Http.request('get', url, query || '')
      if(callback){
         callback(res)
      }else{
         return res
      }      
   }
   static async delete(url, query, callback){
      let res = await Http.request('delete', url, query)
      if(callback){
         callback(res)
      }else{
         return res
      }      
   }
}


var Online = {
   ws: null,
   callback: {},
   async connect(url) {

      let once = System.config.get('once')
                            
      this.ws = new WebSocket(url+`?login=${once}`);
      return new Promise((resolve, reject) => {
         this.ws.onopen = () => {
            console.log("online");
            resolve()
         };

         this.ws.onmessage = (msg) => {
            let data = JSON.parse(decrypt(msg.data))
            let callback = this.callback[data.uri]
            if (callback) {
               delete this.callback[data.uri]
               callback(data.res)
            }
         };

         this.ws.onclose = () => {
            console.log("offline");
         };
      })
   },
   async get(uri, params=null, callback=null) {
      let msg = {uri: uri, _: params}
      let res = null

      if(callback){
         this.callback[uri] = callback
      }else{
         res = new Promise((resolve, _)=>{
            this.callback[uri] = resolve
         })
      }
      this.ws.send(encrypt(msg));   
      return res
   },
   bind() {

   }
}
export {Http, Online}