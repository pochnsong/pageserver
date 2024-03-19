/***
 * cdframe 单页面应用框架 ES6
 */
const VERSION = 'V2023100301'
const STYLE = `
    .pageX{height:100%; width:100%;background-color:#fff;position: absolute; left:0;top:0; overflow-x:hidden;z-index:-1;}
    @keyframes pageXShowleft{from {left: 100%;}to {left: 0;}} @keyframes pageXBackleft{from {left: 0;}to {left: 100%;}}
    @keyframes pageXShowright{from {left: -100%}to {left: 0;}} @keyframes pageXBackright{from {left: 0;}to {left: -100%;}}
    @keyframes pageXShowtop{from {top: -100%}to {top: 0;}} @keyframes pageXBacktop{from {top: 0;}to {top: -100%;}}`;

const SETTINGS = {
    animation: ['left', 'right', 'top', null],
    lazy: [false, true]
}
function cfg(config, k, default_value) {
    let v = config[k] === undefined ? default_value : config[k]
    if (SETTINGS[k].includes(v)) {
        return v
    }

    return SETTINGS[k][0]
}
function attr(obj, name, default_value) {

    let res = obj[name];
    if (res === undefined) {
        res = default_value
    }
    return res
}

let Http = {
    async get(url) {
        return new Promise(function (resolve, reject) {
            let xhr = new XMLHttpRequest();
            xhr.open('GET', url, true);
            xhr.setRequestHeader('If-Modified-Since', '0');
            xhr.responseType = "text";
            xhr.onload = function () {
                if (this.status == 200) {
                    resolve(this.response);
                } else if (this.status == 404) {
                    resolve("");
                }
                else {
                    reject(this.response);
                }
            }
            xhr.send();
        })
    },
}

class Pages {
    getAnimation(v) {
        if (SETTINGS.animation.includes(v)) {
            return v
        }
        return SETTINGS.animation[0]
    }
    config(pages, parents = []) {
        let res = {};

        for (let name in pages) {
            let o = pages[name];
            let path = parents.concat(name);
            let page_name = path.join('.')
            let src = path.join('/')
            res[page_name] = {
                'path': path,
                'name': page_name,
                'load': false,
                'html': '',
                'js': '',
                'css': '',
                'settings': {
                    'html': attr(o, 'html', `${src}/page.html`),
                    'js': attr(o, 'js', `${src}/page.js`),
                    'css': attr(o, 'css', `${src}/page.css`),
                    'lazy': cfg(o, 'lazy', this.lazy),
                    'animation': cfg(o, 'animation', this.animation),
                },
            }
            if (o.pages) {
                let _res = this.config(o.pages, path)
                for (let p in _res) {
                    res[p] = _res[p];
                }
            }

        }
        return res
    }
    async load(page) {
        let href = location.href.split("/")
        href.pop()
        href = href.join("/")
        console.log('加载页面: ' + page.name);
        page.html = await Http.get(`${this.src}${page.settings.html}`)
        page.module = await import(`${href}/${this.src}${page.settings.js}`)
        page.css = await Http.get(`${this.src}${page.settings.css}`)
        page.load = true

        let reg = /<fragment>(\w+)<\/fragment>/g;
        if (reg.test(page.html)) {
            page.html = page.html.replace(reg, this.fragments[RegExp.$1])
        }
    }
    async load_framents() {
        for (let name in this.fragments) {
            this.fragments[name] = await Http.get(`${this.src}${this.fragments[name]}`);
        }
    }

    async get(name) {
        let page = this.pages[name];
        if (!page.load) {
            await this.load(page)
        }
        return page
    }
    check(name) {
        if (this.pages[name]) {
            return true
        }
        return false

    }

    constructor(pages, fragments, src = "", animation = 'left', lazy = false) {
        this.src = src
        this.animation = this.getAnimation(animation)
        this.lazy = lazy
        this.fragments = fragments
        this.pages = this.config(pages)
    }

    async init() {
        for (let name in this.pages) {
            if (!this.pages[name].settings.lazy) {
                await this.get(name)
            }
        }
    }
}
let Dom = {
    initStyle(el) {
        let css = window.getComputedStyle(el);
        let width = css.width;
        let height = css.height;
        if (width == '0px') {
            el.style.width = '100vw'
        }
        if (height == '0px') {
            el.style.height = '100vh'
        }

        let _style = document.createElement("style");
        _style.innerHTML = STYLE;
        document.getElementsByTagName("head")[0].appendChild(_style);
        el.style.overflow = "hidden"
        el.style.position = "relative"
    },
    addStyle(id, content) {
        let el = document.createElement("style");
        el.id = `${id}_css`;
        el.innerHTML = content.replace(/#page/g, `#${id}`);
        document.getElementsByTagName("head")[0].appendChild(el);
    },
    addPage(el, id, html) {
        let div = document.createElement("div");
        div.className = "pageX"
        div.id = id;
        div.innerHTML = html;
        el.appendChild(div);
        return div;
    },
    $Id(id) {
        return document.getElementById(id)
    },
    removeElById(id) {
        let el = this.$Id(id);
        el.parentNode.removeChild(el)
    },
    removeElByClass(class_name) {
        let els = document.getElementsByClassName(class_name)
        for (let el of els) {
            el.parentNode.removeChild(el)
        }
    }
}
class CDFrame {
    getG(key) {
        let value = this.G[key];
        if (value) {
            delete this.G[key];
        }
        return value
    }
    getCurrentObj() {
        return this.objs[this.history[0]]
    }
    getPageName(name) {
        if (name.startsWith("..")) {
            let obj = this.getCurrentObj()
            return name.replace("..", obj ? `${obj.path.slice(0, -2).join('.')}.` : "")
        }
        if (name.startsWith(".")) {
            let obj = this.getCurrentObj()
            return name.replace(".", obj ? `${obj.name}.` : "")
        }
        return name
    }
    async getPage(name) {
        return await this.pages.get(this.getPageName(name))
    }
    constructor(el, config) {
        this.el = Dom.$Id(el);
        Dom.initStyle(this.el);
        if (config.Http != undefined) {
            Http = config.Http
        }
        this.settings = {
            animation: cfg(config.settings, 'animation'),
            lazy: cfg(config.settings, 'lazy'),
            src: attr(config.settings, 'src', attr(config.settings, 'page_path', 'templates/')),
            onLoaded: attr(config.settings, 'onLoaded', function () { console.log("onLoaded") }),
        };
        this.pages = new Pages(
            config.pages, attr(config, 'fragments', {}),
            this.settings.src, this.settings.animation, this.settings.lazy);
        this.G = {};
        this.objs = {};
        this.current = null;
        this.lock = false; //事件锁定
        this.history = [];
        this.preload = config.preload;
        this.init()
    }
    async init() {
        await this.pages.load_framents()

        if (this.preload) {
            await this.preload(this)
        } else {
            await this.pages.init()
        }

        this.settings.onLoaded.call(this);
    }

    destroy_page(page_id) {
        //销毁页面
        console.log('销毁', page_id);
        try {
            let obj = this.objs[page_id];
            delete this.objs[page_id]
            obj.app.onPause && obj.app.onPause()
            obj.app.onDestroy && obj.app.onDestroy()
            obj.app.onStop && obj.app.onStop()
            obj.app = undefined;
            Dom.removeElById(page_id);
            Dom.removeElById(`${page_id}_css`);
        } catch (e) {
            console.error(e)
        }
    }
    async new_page(name, para, animation) {
        console.log('打开新页面 ', name, this.lock);
        let page = await this.getPage(name);
        if (!page) {
            console.warn("页面不存在: " + name)
            return
        }

        if (this.lock) { return }
        this.lock = true

        name = page.path.join('.')
        let page_id = 'page_' + (new Date()).valueOf();
        if (animation === undefined) { animation = page.settings.animation }

        let app = new page.module.default()
        
        if (app == null) {
            return
        }
        this.history.unshift(page_id);
        let obj = {
            'path': copy(page.path),
            'name': name,
            'page_id': page_id,
            'app': app,
            'animation': animation,
        };
        this.objs[page_id] = obj;
        Dom.addStyle(page_id, page.css); //添加css
        Dom.addPage(this.el, page_id, page.html);//添加dom
        this.current = app

        try {
            app.onCreate && app.onCreate(page_id, para); //运行JS
        } catch (e) {
            console.error(e)
        }
        let page_dom = document.getElementById(page_id);
        page_dom.style.zIndex = this.history.length;


        //动画
        if (animation && this.history.length > 1) {
            let self = this;
            function animationEndFn() {
                page_dom.removeEventListener("webkitAnimationEnd", animationEndFn);
                self.lock = false;
                try {
                    app.onShow && app.onShow(obj.app);
                } catch (e) {
                    console.error(e)
                }
                self = undefined
            }
            page_dom.addEventListener("webkitAnimationEnd", animationEndFn)
            page_dom.style.animation = `pageXShow${animation} 0.3s`;

        } else {
            switch (animation) {
                case 'top':
                    page_dom.style.top = 0;
                    break
                case 'right':
                default:
                    page_dom.style.left = 0;
            }
            Dom.removeElByClass("pageX reset-page-cover")
            try {
                app.onShow && app.onShow(app);
            } catch (e) {
                console.error(e)
            }
            this.lock = false
        }
        return page_id;

    }

    go_back(page_tag, animation) {
        //page_tag = page_id or page_name
        if (this.history.length == 1) {
            return
        }

        let page_id = this.history[0]
        let obj = this.objs[page_id];

        if (obj.app.onBack && !obj.app.onBack.call()) {
            return
        }

        try {
            obj.app.onPause && obj.app.onPause.call()
        } catch (e) {
            console.error(e)
        }

        let page_dom = Dom.$Id(page_id);
        this.history.shift()
        if (page_tag != undefined) {
            if (page_id != page_tag || obj.name != page_tag) {
                while (this.history.length > 1) {
                    let _page_id = this.history[0];
                    let _obj = this.objs[_page_id];
                    if (_page_id === page_tag || _obj.name == page_tag) break;
                    this.history.shift();
                    this.destroy_page(_page_id);
                }
            }

        }

        if (animation === undefined) { animation = obj.animation }

        this.current = this.objs[this.history[0]].app;

        if (animation) {
            page_dom.addEventListener("webkitAnimationEnd", () => {
                this.destroy_page(page_id);
                this.current.onShow && this.current.onShow(this.current);
            })
            page_dom.style.animation = 'pageXBack' + animation + ' 0.3s';

        } else {
            switch (animation) {
                case 'top':
                    page_dom.style.top = '-100%';
                    break
                case 'right':
                    page_dom.style.left = '-100%';
                    break
                default:
                    page_dom.style.left = '100%';
            }
            this.destroy_page(page_id);
            this.current.onShow && this.current.onShow(this.current);
        }
    }
    reset_page(name, para) {
        //重置页面, 无动画
        name = this.getPageName(name)
        let page_id = this.history[0];
        let obj = this.objs[page_id];
        console.log("重置", name)
        if (obj.name == name) { return }
        this.history.shift();
        this.destroy_page(page_id);

        //添加遮罩dom
        let div = document.createElement("div");
        div.classList.add("pageX", "reset-page-cover");
        div.style.backgroundColor = "#fff";
        div.style.zIndex = this.history.length;
        this.el.appendChild(div);
        this.new_page(name, para, null);
    }
    start_page(name, para) {
        //重置页面, 无动画
        while (self.history.length > 0) {
            let page_id = self.history.shift();
            self.destroy_page(page_id);
        }
        self.new_page(name, para, null);
    }
}
window.copy = function (v) {
    return JSON.parse(JSON.stringify({ _: v }))._
}

export {CDFrame, VERSION}
