/*
config = {
    el: "#menu",
    header: {html: "", onclick: null},
    footer: {html: "", onclick: null},
    items: [
        {name: 'index', label: '首页', onclick: null},
        {page: 'client', label: '新客管理', onclick: null},
        {page: 'goods', label: '礼品管理', onclick: null},
    ],
    show: true,
    onclick(menu_item){}
}*/
function Menu(config) {
    this.ver = "20211212";
    function div(classname, data) {
        let el = document.createElement('div')
        if (classname) {
            el.className = classname
        }
        if (data) {
            el.setAttribute('data-_', data)
        }
        return el
    }
    function add_class($el, classname) {
        if ($el) { 
            $el.className += ` ${classname}`
            return true
        }else{
            return false
        }
    }
    function rm_class($el, classname) {
        let res = false
        if ($el){
            let arr = []
            for (let x of $el.className.split(" ")) {
                if (x == classname) {
                    res = true
                }else{
                    arr.push(x)
                }
            }
            $el.className = arr.join(" ");
        }
        return res
    }
    function toggle_class($el, classname){
        console.log('toggle_class')
        if(!rm_class($el, classname)){
            add_class($el, classname)
        }
    }
    function get_menu_item(name, items) {
        items = items || config.items
        for (let cfg of items) {
            if (name == cfg.name) {
                return copy(cfg)
            }

            if (cfg.items) {
                let item = get_menu_item(name, cfg.items)
                if (item) {
                    return item
                }
                continue
            }


        }
        return null

    }
    function create_items(items_list, level) {
        /**
            <div class="items">
                <div class="item">
                    <button >{{label}}</button>
                </div>
                <div class="item">
                    <button class="wrapper">{{label}}</button>
                    <div class="items">...</div>
                </div>     
            </div>
 
         */
        let items
        if (level > 0) {
            items = div('items')
            items.style.height = '0px'
        } else {
            items = div('items')
        }
        for (let cfg of items_list) {
            let item = div('item')
            let btn = document.createElement('button')
            btn.style.paddingLeft = `${1 + 1 * level}rem`
            if (!cfg.icon) {
                cfg.icon = cfg.items ? "fas fa-tags" : "fas fa-tag"
            }

            btn.innerHTML = `<div class="no-event"><i class="${cfg.icon}"></i><span class="label">${cfg.label}</span></div>`

            item.appendChild(btn)
            if (cfg.items) {
                btn.className = "wrapper"
                btn.setAttribute('data-_', 'items')
                item.appendChild(create_items(cfg.items, level + 1))
            } else {
                btn.setAttribute('data-_', 'item')
                btn.setAttribute('data-item', cfg.name)
            }
            items.appendChild(item)
        }
        return items
    }

    this.toggle = function ($el, $button) {
        let fid = null;
        function _toggle() {
            if ($el.style.height == "0px") {
                $el.style.height = `${$el.scrollHeight}px`
                add_class($button, 'expand')
            } else {
                $el.style.height = "0px"
                rm_class($button, 'expand')
            }
        }
        function transitionend() {
            this.removeEventListener("transitionend", transitionend);
            clearInterval(fid)
            if ($el.style.height != '0px') {
                $el.style.height = 'auto'
            }
        }
        $el.addEventListener("transitionend", transitionend)

        if ($el.style.height == "") {
            $el.style.height = "0px"
        }
        if ($el.style.height == "auto") {
            $el.style.height = `${$el.scrollHeight}px`
        }
        fid = setTimeout(_toggle, 1)

    }

    //console.log(config.el)

    let el = document.querySelector(config.el)
    el.innerHTML=""
    el.className = "menu"
    el.style.backgroudColor = config.backgroudColor || '#345274'
    let bar = div('bar')
    bar.innerHTML = `<div data-_="ldiv"><i class="fas fa-bars"></div>`
    el.appendChild(bar)

    let header = div('header')
    header.innerHTML = `<div>${config.header.html}</div><i class="fas fa-outdent" data-_="bar"></i>`
    header.onclick = config.header.onclick
    el.appendChild(header)
    let root = div('root')
    el.appendChild(root)
    let items = create_items(config.items, 0)
    root.appendChild(items)


    if (config.footer) {
        let footer = div('footer', 'footer')
        footer.innerHTML = config.footer.html

        let rdiv = div('', 'footer')
        rdiv.innerHTML = config.footer.html
        bar.appendChild(rdiv)
        el.appendChild(footer)
    }
    el.onclick = (event) => {
        let $el = event.target
        let target = $el.getAttribute('data-_')
        if (target == 'bar') {
            toggle_class(el, 'sidebar')
        }else if (target == 'ldiv') {
            //展开    
            this.toggle(items)
        } else if (target == 'footer') {
            //退出
            if (config.footer.onclick) {
                config.footer.onclick()
            }
        } else if (target == 'items') {
            let sub = $el.parentNode.querySelector('.items');
            this.toggle(sub, $el)
        }
        else if (target == 'item') {
            let name = $el.getAttribute('data-item')
            let item = get_menu_item(name)
            if (item) {
                window.location.hash = name
                let selected_list = el.querySelectorAll('.selected')
                for (let _el of selected_list) {
                    rm_class(_el, 'selected')
                }
                add_class($el, 'selected')
                config.onclick(item)
            }
        }

    }

    this.show = (v) => {
        if (v) {
            add_class(el, 'show')
            //el.style.width="250px"
        } else {
            rm_class(el, 'show')
            //el.style.width="0"
        }
    }

    this.click = (name) => {
        //console.log(name)
        let item = get_menu_item(name)
        if (item) {
            config.onclick.call(this, item)
        }
    }
    this.select=(name)=>{
        
        let _el = el.querySelector(`button[data-item="${name}"]`)
        if (!_el) { return }
        
        let _parent = _el.parentNode.parentNode
        if (_parent.style.height == '0px') {
            this.toggle(_parent, _parent.parentNode.querySelector('.wrapper'))
        }
        
        add_class(_el, 'selected')
        
        this.click(name)
    }
    config.created && config.created.call(this)

}

var menu = null;