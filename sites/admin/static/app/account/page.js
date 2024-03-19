export default class {
    onCreate(page_id) {
        this.app = new Vue({
            el: `#${page_id}`,
            data: {
                object_list: [],
                object_count: 0,
                current_page: 1,
                waiting: {
                    loading: true,
                },
                filters: {
                    skip: 0,
                    limit: 10,
                },
                rm_objs: null,
            },
            created() {
                this.get_object_list()
            },
            methods: {
                get_next_page(v) {
                    let skip = this.filters.skip + this.filters.limit * v;
                    if (skip < 0) {
                        $toast("已经为首页")
                        return
                    }
                    if (skip >= this.object_count) {
                        $toast("已经为末页")
                        return
                    }
                    this.current_page += v
                    this.filters.skip = skip
                    this.get_object_list()
                },
                get_last_page() {
                    return Math.ceil(this.object_count / this.filters.limit) || 1
                },
                get_object_list() {
                    this.current_page = parseInt(this.filters.skip/ this.filters.limit)+1
                    
                    this.waiting.loading = true
                    Http.get(`/admin/api/user/list/`, this.filters, data => {
                        console.log(copy(data))
                        this.waiting.loading = false
                        if (data.status == 'OK') {
                            if (data.count) {
                                this.object_count = data.count
                            }
                            this.object_list = data.object_list
                        } else {
                            $toast(data.errors)
                        }
                    })
                },
                edit(obj) {
                    let para = {
                        obj: obj,
                        callback: this.get_object_list,
                    }
                    main.new_page('.edit', para)
                },
                set_fields(){
                    main.new_page(".fields", {
                        fields: this.fields,
                        local_config: this.local_config,
                    })
                }
            }
        })
    }
    onShow() {
    }
    onStop() {
        //console.log('stop')
        this.app.$destroy()
    }
}
