export default class {
    onCreate(page_id) {
        this.app = new Vue({
            el: `#${page_id}`,
            data: {
                object_list: [],
                waiting: {
                    loading: true,
                },
            },
            created() {
                this.get_object_list()
            },
            methods: {
                get_object_list() {
                    
                    this.waiting.loading = true
                    Http.get(`/admin/api/cache/dbs/`, data => {
                        this.waiting.loading = false
                        if (data.status == 'OK') {
                            this.object_list = data.result
                        } else {
                            $toast(data.errors)
                        }
                    })
                },
                edit(obj) {

                    let para = {
                        model_name: copy(this.model_name),
                        fields: this.fields,
                        obj: obj,
                        callback: this.get_object_list,
                    }
                    main.new_page('.edit', para)
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
