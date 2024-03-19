export default class{
    onCreate(page_id){

        this.app = new Vue({
            el: '#'+page_id,
            data: {
                profile: {}
            },
            created() {
                this.get_profile()
            },
            methods: {
                get_profile() {
                    Host.get("/admin/api/login/profile/", data=>{
                        if(data.status=="OK"){
                            this.profile = data.profile
                        }else{
                            $toast(data.errors)
                        }
                    })
                },
            }
        })
    }
    onShow(){
    }
    onStop(){
        console.log('stop')
        this.app.$destroy()
    }
}