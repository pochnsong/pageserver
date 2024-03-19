var System = {
    G: {},
    PREFIX: "a:",
    host: {
        get() {
            return ""
        }
    },
    login: {
        //登录信息
        get() {
            return System.config.get("loginid");
        },
        set(loginid) {
            System.config.set('loginid', loginid)
        },
    },
    cache: {
        // 缓存
        set(key, value) {
            if (value == undefined) {
                value = key;
                key = "";
            }
            System.G[key] = JSON.stringify({ _: value })

        },
        get(key="") {
            try {
                return JSON.parse(System.G[key])._;
            } catch (e) {
                return undefined;
            }
        },
    },
    config: {
        get(name) {
            name = System.PREFIX+name
            try {
                return JSON.parse(localStorage.getItem(name))._;
            } catch (e) {
                return null;
            }
        },
        set(name, value) {
            name = System.PREFIX+name
            localStorage.setItem(name, JSON.stringify({ _: value }));
        },
        remove(name) {
            name = System.PREFIX+name
            localStorage.removeItem(name);
        },

    }
};
