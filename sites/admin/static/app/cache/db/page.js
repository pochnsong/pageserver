export default class {
    onCreate(page_id, db) {
        this.app = new Vue({
            el: `#${page_id}`,
            data: {
                object_list: [],
                object_count: 0,
                waiting: {
                    loading: true,
                },
                filters: {
                    db: db,
                    cursor: 0,
                    limit: 10,
                },
                current_page: 1,
                value: {
                    show: false,
                    k: '',
                    v: '-',
                    t: null,
                    ttl: '-',
                },
            },
            created() {
                this.getList()
            },
            methods: {
                get_next_page(v) {
                    let cursor = this.filters.cursor + this.filters.limit * v;
                    if (cursor < 0) {
                        $toast("已经为首页")
                        return
                    }
                    if (cursor >= this.object_count) {
                        $toast("已经为末页")
                        return
                    }
                    this.current_page += v
                    this.filters.cursor = cursor
                    this.getList()
                },
                get_last_page() {
                    return Math.ceil(this.object_count / this.filters.limit) || 1
                },
                getList() {
                    this.current_page = parseInt(this.filters.cursor/ this.filters.limit)+1
                    
                    this.waiting.loading = true
                    Http.get(`/admin/api/cache/keys/`, this.filters, data => {
                        this.waiting.loading = false
                        if (data.status == 'OK') {
                            if (data.size!=undefined) {
                                this.object_count = data.size
                            }
                            this.object_list = data.keys
                        } else {
                            $toast(data.errors)
                        }
                    })
                },
                getValue(key) {
                    this.value={
                        show: true,
                        k: key,
                        v: '-',
                        t: null,
                        ttl: '-',
                    }
                    Http.get(`/admin/api/cache/value/`, {db: this.filters.db, key: key}, data => {
                        this.waiting.loading = false
                        console.log(data)
                        if (data.status == 'OK') {
                            this.value.v = data.value
                            this.value.t = data.type
                            this.value.ttl = data.ttl
                        } else {
                            $toast(data.errors)
                        }
                    })
                },
                deleteCache(){
                    Http.post('/admin/api/cache/delete/', {db: this.filters.db, key: this.value.k}, data => {
                        if (data.status == 'OK') {
                            this.value.show = false
                            this.getList()
                        } else {
                            $toast(data.errors)
                        }
                    })
                }
            }
        })
    }
    onDestroy() {
        this.app.$destroy()
    }
}
