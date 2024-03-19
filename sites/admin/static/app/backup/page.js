export default class {
    onCreate(page_id) {
        this.app = new Vue({
            el: `#${page_id}`,
            data: {
                selected_all: false,
                selected: [],
                object_list: [],   
                message: {
                    list: [],
                    lock: false,
                },             
                waiting: {
                    loading: true,
                },
            },
            created() {
                this.getObjectList()
            },
            watch:{
                selected(val, old){
                    if(this.selected.length!=this.object_list.length){
                        this.selected_all = false
                    }else{
                        this.selected_all = true
                    }
                }
            },
            methods: {
                selectAll(){
                    this.selected_all = !this.selected_all
                    if(this.selected_all){
                        for(let o of this.object_list){
                            this.selected.push(o.model_name)
                        }
                    }else{
                        this.selected = []
                    }
                },
                getObjectList() {
                    Http.get("/admin/api/model/", data=>{
                        this.waiting.loading = false
                        if(data.status=="OK"){
                            this.object_list = data.model_list
                            return
                        }
                    })
                },
                async exportData(){
                    if(!this.selected.length){
                        $toast('没有选择任何数据表')
                        return
                    }
                    let data = await Http.get("/admin/api/login")
                    if(data.status != "OK"){
                        $toast("登录错误")
                        return
                    }

                    let url = window.location.origin+`/admin/api/backup/export/?login=${data.once}`;

                    let form = document.createElement('form');
                    form.id = 'form';
                    form.name = 'form';
                    document.body.appendChild (form);
                    for (let v of this.selected) {
                        let input = document.createElement('input')
                        input.type='hidden'
                        input.name = 'model';
                        input.value = v
                        form.appendChild(input)

                    };
                    form.method = 'post'; 
                    form.action = url; 
                    form.submit();
                    document.body.removeChild(form)
                },
                async importData(){
                    if(this.$refs.inputFile.files.length == 0){
                        $toast("请选择导入文件")
                        return
                    }
                    let file = this.$refs.inputFile.files[0]

                    let data = await Http.upload('/admin/api/upload/block/', file, file.name, (stat) => {
                        //x.process = (stat.i / stat.total) * 100
                    })
                    if(data.status != "OK"){
                        $toast("上传文件失败")
                        return
                    }
                    let login = await Http.get("/admin/api/login")
                    if(login.status != "OK"){
                        $toast("获取登录凭证失败")
                        return
                    }
                    let protocol = location.protocol=='https:'?'wss:':'ws:'
                    let ws = new WebSocket(`${protocol}//${location.host}/admin/ws/backup/import?login=${login.once}`)
                    ws.onopen = ()=>{
                        ws.send(JSON.stringify({fk: data.file_key}))
                    }
                    ws.onmessage = (e)=>{
                        try{
                            let data = JSON.parse(e.data)
                            this.message.list.push(data)
                        }catch{
                            console.log(e.data)
                        }
                        
                    }
                    ws.onclose = ()=>{
                        console.log('close')
                    }

                },
            }
        })
    }
    onShow() {
    }
    onStop() {
        this.app.$destroy()
    }
}
