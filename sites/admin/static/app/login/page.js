import {getKeyExchange, setKey, encrypt} from "../../libs/secrets.js"


export default class {
    onCreate(page_id, params) {
        this.app = new Vue({
            el: '#' + page_id,
            data: {
                form: {
                    usr: '',
                    pwd: '',
                },
                now: new Date(),
                success_page: 'index',
                runid: null,
            },
            created() {
                this.check_login()
                this.runid = setInterval(this.update_now, 1000)
            },
            methods: {
                update_now() {
                    this.now = new Date()
                },
                success() {
                    main.reset_page(this.success_page)
                },
                check_login() {
                    let login = System.login.get();
                    if (login && login.sm4) {
                        setKey(login.sm4)
                    }
              
                    Http.get("/admin/api/login/", (data) => {
                        if (data.status == "OK") {
                            System.config.set('once', data.once)
                            this.success()
                        }else{
                            //setKey(null)
                            //System.login.set(null)
                        }
                    })
                },
                login() {
                    let [pubkey, key] = getKeyExchange(document.head.querySelector("[name=pubkey]").content)
                    setKey(key)
                    System.login.set(null)
                    if(this.form.usr.length==0 || this.form.pwd.length == 0){
                        return
                    }
                    System.login.set({sm4: key})
                    let form = new FormData()
                    form.append('data', encrypt(this.form))
                    form.append('pubkey', pubkey)
                    Http.post("/admin/api/login/", form, (data)=>{
                        if (data.status == 'OK') {
                            let loginid = data.loginid
                            loginid.sm4 = key
                            System.login.set(loginid)
                            System.config.set('once', data.once)
                            this.success()
                        } else {
                            $toast("用户名或密码错误")
                        }
                    })
                }
            }
        })
    }
    onShow() {
    }
    onStop() {
        clearInterval(this.app.runid)
        this.app.$destroy()
    }
}