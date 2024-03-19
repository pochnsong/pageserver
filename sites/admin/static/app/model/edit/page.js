export default class{
    onCreate(page_id, para){

        this.app = new Vue({
            el: `#${page_id}`,
            data: {
                model_name: para.model_name,
                form: {},
                obj: copy(para.obj),
                files: {},
                fields: copy(para.fields),
                waiting: {
                    submit: false,
                },
            },
            created() {
                this.init()
            },
            methods: {
                init(){
                    let form = {}
                    for (let field of this.fields) {
                        form[field.name] = field.default
                        if(field.choice){
                            field.type = "select"
                        }
                        if(field.max_length){
                            this.$watch(`form.${field.name}`, function(newValue, oldValue){
                                if (newValue.length>field.max_length){
                                    this.form[field.name] = newValue.slice(0, field.max_length)
                                }
                            })
                        }
                    }

                    if(this.obj){
                        this.form = copy(this.obj)
                    }else{
                        this.form = form
                    }
                },
                getWords(field){
                    return this.form[field.name].length
                },
                get_label(field) {
                    return field.label || field.name
                },    
                select_file(event, field){
                    var files = event.target.files;
                    for(let f of files){
                        this.files[field.name] = f
                    }
                },
    
                get_form_data(action) {
                    let data = new FormData()
                    for (let field of this.fields) {
                        let name = field.name;
                        if (field.type == 'auto' && action == 'new') continue;
                        if (field.nullable == false && this.form[name] === "") {
                            $toast("请填写" + this.get_label(field))
                            return null
                        }
                        if(this.files[name]!=undefined){
                            data.set(name, this.files[name])
                        }else{
                            data.set(name, this.form[name])
                        }
                    }
    
                    return data
    
                },
                submit() {                    
                    let action = this.obj?'edit':'new'
                    let form_data = this.get_form_data(action)
                    if (form_data == null) return;
                    this.waiting.submit = true

                    Http.post(`/admin/api/admin?model=${this.model_name}&action=${action}`, form_data, data => {
                        console.log(data)
                        this.waiting.submit = false
                        if (data.status == 'OK') {
                            para.callback()
                            main.go_back()
                        } else {
                            $toast(data.errors)
                        }
                    })
                },
                
                delete_obj(){
                    this.waiting.submit = true
                    let pk = null
                    for (let field of this.fields) {
                        if (field.primary_key){
                            pk = field.name
                        };
                    }
    
                    Http.delete(`/admin/api/admin`, {model: this.model_name, pk: this.form[pk]}, data => {
                        this.waiting.submit = false
                        if (data.status == 'OK') {
                            para.callback()
                            main.go_back()
                        } else {
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