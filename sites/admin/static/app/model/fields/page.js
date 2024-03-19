export default class{
    onCreate(page_id, para){
        document.getElementById(page_id).style.backgroundColor="rgba(0,0,0,0)"
        this.app = new Vue({
            el: `#${page_id}`,
            data: {
                fields: para.fields,
            },
            created() {
            },
            methods: {
                get_label(field) {
                    return field.label || field.name
                },
                get_label(field) {
                    return field.label || field.name
                },
                toggle_field(field) {
                    this.$set(field, 'show', !field.show)
                    let cfg = para.local_config()
                    cfg.fields_hidden[field.name] = field.show
                    para.local_config(cfg)
                },
            }
        })
    }
    onShow(){
    }
    onStop(){
        this.app.$destroy()
    }
}