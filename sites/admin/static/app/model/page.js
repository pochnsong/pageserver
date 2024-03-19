export default class {
    onCreate(page_id, model_obj) {
        menu.current = 'model'

        this.app = new Vue({
            el: `#${page_id}`,
            data: {
                object_list: [],
                object_count: 0,
                current_page: 1,
                model_obj: model_obj,
                model_name: model_obj.model_name,
                waiting: {
                    loading: true,
                },
                filters: {
                    skip: 0,
                    limit: 10,
                },
                selected: [],
                selected_all: false,
                pk: "id",
                fields: {},
                columns: [],
                is_delete_objs: false,
                sizes:{},
            },
            watch:{
                selected_all(val, old){
                    if(val){
                        for(let o of this.object_list){
                            this.selected.push(this.get_pk(o))
                        }
                    }else{
                        this.selected = []
                    }
                }
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
                get_label(field) {
                    return field.label || field.name
                },
                set_size(event, obj, field){
                    let el = event.target
                    this.sizes[obj[field.name]] = `${el.naturalWidth}×${el.naturalHeight}`
                    this.$forceUpdate()
                },
                get_size(obj, field){
                    return this.sizes[obj[field.name]]
                },
                set_size(event, obj, field){
                    let el = event.target
                    this.sizes[obj[field.name]] = `${el.naturalWidth}×${el.naturalHeight}`
                    this.$forceUpdate()
                },
                get_size(obj, field){
                    return this.sizes[obj[field.name]]
                },
                get_value(obj, field) {
                    let res = obj[field.name]
                    if(field.choice){
                        for(let o of field.choice){
                            if(o[0] == res){
                                return o[1]
                            }
                        }
                    }
                    if (field.type == "timestamp") {
                        return Display.datetime(res)
                    }
                    if (field.type == "image") {
                        return `/media/${res}`
                    }
                    res = '' + res
                    if (res.length > 32) {
                        res = res.substr(0, 32) + ' ...'
                    }
                    return res
                },
                get_object_list() {
                    this.current_page = parseInt(this.filters.skip/ this.filters.limit)+1                    
                    this.waiting.loading = true
                    let query = copy(this.filters)
                    query['model'] = this.model_name
                    Http.get(`/admin/api/admin/`, query, data => {
                        this.waiting.loading = false
                        if (data.status == 'OK') {
                            if (data.count) {
                                this.object_count = data.count
                            }

                            if (data.fields) {
                                let columns = []
                                let cfg = this.local_config()
                                for (let field of data.fields) {
                                    columns.push(field.name)
                                    field.show = true
                                    if (field.name in cfg.fields_hidden) {field.show = cfg.fields_hidden[field.name]}
                                    if (field.primary_key) {this.pk = field.name}
                                }
                                this.fields = data.fields
                                this.columns = columns
                            }
                            this.object_list = zip(this.columns, data.object_list)
                        } else {
                            $toast("errors"+data.errors)
                        }
                    })
                },
                local_config(v) {
                    let key = `model-${this.model_name}`;
                    if (v == undefined) {
                        let cfg = System.config.get(key)
                        if (!cfg) {
                            cfg = {
                                fields_hidden: {}
                            }
                        }
                        return cfg
                    } else {
                        System.config.set(key, v)
                    }
                },
                toggle_field(field) {
                    this.$set(field, 'show', !field.show)
                    let cfg = this.local_config()
                    cfg.fields_hidden[field.name] = field.show
                    this.local_config(cfg)
                },
                model_edit(obj) {

                    let para = {
                        model_name: copy(this.model_name),
                        fields: this.fields,
                        obj: obj,
                        callback: this.get_object_list,
                    }
                    main.new_page('.edit', para)
                },
                get_pk(obj){
                    return obj[this.pk]
                },
                delete_objs(ok) {
                    if (!ok) {
                        this.is_delete_objs = true
                        return
                    }

                    Http.post(`/admin/api/delete?model=${this.model_name}`, {pks: this.selected }, data => {
                        if (data.status == 'OK') {
                            this.selected_all = false
                            this.get_object_list()
                            this.is_delete_objs = false
                        } else {
                            $toast(data.errors)
                        }
                    })

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
    onShow(self) {
    }
    onDestroy(self) {
        console.log('destroy')
        this.app.$destroy()
    }
}
