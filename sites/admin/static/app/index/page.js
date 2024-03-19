export default class {
    onCreate(page_id) {
        this.app = new Vue({
            el: '#' + page_id,
            data: {
                profile: {},
                info: {},
                now: null,
                memory: null,
                top: null,
                media: {
                    size: '-',
                }
            },
            created() {
                this.getModelList()
                this.init()
            },
            methods: {
                async init() {
                    await Online.connect(`${location.protocol == 'https:' ? 'wss:' : 'ws:'}//${location.host}/admin/ws/online/`)
                    this.getOverview()
                    this.getMemory()
                    this.getTop()
                    Online.get("/media/size", null, (data) => {
                        this.media.size = data.size
                    })
                },
                getOverview() {
                    Online.get("/connect/info", null, data => {
                        this.info = data.info
                        this.now = data.now
                    })
                },
                async getMemory() {
                    this.memory = await this.getCMD('memory')
                },
                async getTop() {
                    this.top = await this.getCMD('top')
                },
                async getCMD(cmd) {
                    let data = await Online.get(`/${cmd}/info`, null)
                    let info = []
                    for (let x of data.info) {
                        x = x.replace(/ /g, '&ensp;')
                        info.push(x)
                    }
                    return {
                        info: info,
                        now: data.now,
                    }

                },
                configMenu(model_items) {
                    menu = new Menu({
                        el: "#menu",
                        items: [
                            { label: '概览', name: 'index', page: 'index', icon: 'fa-solid fa-computer' },
                            { label: '数据库', items: model_items, icon: 'fa-solid fa-database' },
                            { label: '管理员', name: 'user', page: 'account', icon: 'fa-solid fa-users-cog' },
                            { label: '缓存', name: 'cache', page: 'cache', icon: 'fa-solid fa-server' },
                            { label: '备份', name: 'backup', page: 'backup', icon: 'fa-solid fa-cloud-arrow-down' },
                            { label: '我的账号', name: 'my', page: 'my', icon: 'fa-solid fa-user' }
                        ],
                        header: {
                            html: "数据中心"
                        },
                        footer: {
                            html: "退出",
                            onclick() {
                                System.login.set(null)
                                menu.show(false)
                                main.reset_page('login')
                            }
                        },
                        onclick(item) {
                            let name = item.name
                            let page = item.page
                            main.go_back("index")
                            if (name != "index") {
                                main.new_page(page, item.para)
                            }
                        },
                        created() {
                            if (window.location.hash) {
                                //启动上次页面
                                let name = window.location.hash.substr(1)
                                this.select(name)
                            }
                        }
                    })
                    menu.show(true)

                },
                getModelList() {
                    Http.get("/admin/api/model/", data => {
                        console.log(data)
                        if (data.status != "OK") {
                            return
                        }
                        let model_items = []
                        for (let obj of data.model_list) {
                            model_items.push({
                                name: '@' + obj.model_name,
                                label: obj.label,
                                page: 'model',
                                para: obj,
                                icon: 'fa-solid fa-table',
                            })
                        }
                        this.configMenu(model_items)

                    })
                },
            }
        })
    }
    onShow() {
    }
    onDestroy() {
        this.app.$destroy()
    }
}