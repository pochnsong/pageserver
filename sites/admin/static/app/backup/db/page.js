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
                value: null,
            },
            created() {
                this.get_object_list()
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
                    this.get_object_list()
                },
                get_last_page() {
                    return Math.ceil(this.object_count / this.filters.limit) || 1
                },
                get_object_list() {
                    this.current_page = parseInt(this.filters.cursor/ this.filters.limit)+1
                    
                    this.waiting.loading = true
                    Host.get(`/admin/api/cache/keys/`, this.filters, data => {
                        this.waiting.loading = false
                        console.log(data)
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
                get_value(key) {
                    this.value={
                        k: key,
                        v: '-',
                        t: null,
                        ttl: '-',
                    }
                    Host.get(`/admin/api/cache/value/`, {db: this.filters.db, key: key}, data => {
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
            }
        })
    }
    onShow() {
    }
    onStop() {
        this.app.$destroy()
    }
}
