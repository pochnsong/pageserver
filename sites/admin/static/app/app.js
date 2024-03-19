import { CDFrame } from "../libs/cdframe.es6.js";
import { Http, Online } from './libs/paras.js'

window.Http = Http
window.Online = Online

window.$ = function (el) {
	return document.querySelector(el)
}
window.$Id = function (_id) {
	return document.getElementById(_id)
}

window.zip = function (columns, dataset, update) {
	let res = []
	for (let d of dataset) {
		let obj = columns.reduce((o, k, i) => {
			if (k.indexOf("$") > -1) {
				k = k.split("$")
				if (!o[k[0]]) {
					o[k[0]] = {}
				}
				o[k[0]][k[1]] = d[i]
			} else {
				o[k] = d[i]
			}
			return o;
		}, {});
		update && update(obj)
		res.push(obj)
	}
	return res
}

var APP_CONFIG = {
	pages: {
		login: {},
		index: {},
		model: {
			pages: {
				edit: {
					animation: null,
				},
				fields: {
					animation: 'left',
				}
			}
		},
		account: {
			pages: {
				edit: {}
			}
		},
		cache: {
			pages: {
				db: {}
			}
		},
		backup: {},
		my: {},
	},
	settings: {
		animation: 'top',
		lazy: true,
		page_path: 'static/app/',
		onLoaded() {
			this.new_page("login");
		}
	},
}

window.main = new CDFrame("main", APP_CONFIG)