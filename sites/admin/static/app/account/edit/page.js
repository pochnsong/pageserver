export default class{
    onCreate(page_id, para){
        document.getElementById(page_id).style.backgroundColor="rgba(0,0,0,0)"
        this.app = new Vue({
            el: `#${page_id}`,
            data: {
                form: {},
                repeat: '',
                obj: copy(para.obj),
                reset:{
                    show: false,
                    password: '',
                    repeat: '',
                },
                waiting: {
                    submit: false,
                },
            },
            created() {
                this.init()
            },
            watch:{
                'form.username':{
                    handler(newValue, oldValue){
                        if (newValue.length>32){
                            this.form.username = newValue.slice(0, 32)
                        }
                    }
                },
                'form.password':{
                    handler(newValue, oldValue){
                        if (newValue.length>128){
                            this.form.password = newValue.slice(0, 128)
                        }
                    }
                },
                'form.nickname':{
                    handler(newValue, oldValue){
                        if (newValue.length>16){
                            this.form.nickname = newValue.slice(0, 16)
                        }
                    }
                }
            },
            methods: {
                getObj(){
                    Http.get('/admin/api/user/list/', {id: this.obj.id}, data => {
                        if (data.status == 'OK') {
                            this.obj = data.object_list[0]
                            this.init()
                        } else {
                            $toast(data.errors)
                        }
                    })
                },
                init(){
                    if(this.obj){
                        this.form = {
                            id: this.obj.id,
                            nickname: this.obj.nickname,
                            is_super: this.obj.is_super? true : false,
                            is_active: this.obj.is_active? true: false,
                        } 
                    }else{
                        this.form = {
                            username: '',                            
                            nickname: '',
                            password: '',
                            is_super: false,
                            is_active: true,
                        }    
                    }
                },
                submit() {
                    try{
                        if(!this.obj){
                            if(this.form.username.length<4){                                
                                throw "登录帐号长度不能小于4位"
                            }
                            if(this.form.password.length<8){
                                throw "密码长度不能小于8位"
                            }
                            if(this.repeat!=this.form.password){
                                throw '密码重复错误'
                            }

                        }    
                    }catch(e){
                        $toast(e)
                        return
                    }
                    this.waiting.submit = true
                    Http.post('/admin/api/user/edit', this.form, data => {
                        if (data.status == 'OK') {
                            main.go_back()
                            para.callback()
                        } else {
                            $toast(data.errors)
                            this.waiting.submit = false
                        }
                    })
                },
                resetPassword(){
                    this.reset.show = true
                    this.reset.password = ''
                    this.reset.repeat = ''
                },
                submitPassword() {
                    try{
                        if(!this.obj){
                            if(this.reset.password.length<8){
                                throw "密码长度不能小于8位"
                            }
                            if(this.reset.repeat!=this.reset.password){
                                throw '密码重复错误'
                            }

                        }    
                    }catch(e){
                        $toast(e)
                        return
                    }
                    this.waiting.submit = true
                    Http.post('/admin/api/user/reset/password', {id: this.obj.id, password: this.reset.password}, data => {
                        this.waiting.submit = false
                        if (data.status == 'OK') {
                            if (data.self){
                                $reLogin("密码变更成功，当前所有凭证已失效，点击确定重新登录")
                            }else{
                                this.getObj()
                                $toast("密码变更成功")
                                this.reset.show = false    
                            }
                        } else {
                            $toast(data.errors)
                        }
                    })
                },
                delete_obj(){
                    this.waiting.submit = true
    
                    Http.delete(`/admin/api/user/edit`, {pk: this.obj.id}, data => {
                        if (data.status == 'OK') {
                            main.go_back()
                            para.callback()
                        } else {
                            this.waiting.submit = false
                            $toast(data.errors)
                        }
                    })
                }
            }
        })
    }
    onShow(){
    }
    onStop(){
        this.app.$destroy()
    }
}