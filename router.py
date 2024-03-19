import functools
import inspect
import re

from .utils.module_loading import import_string
from .utils.asynctools import sync_to_async

__all__ = ['UrlRouter', 'include']


class UrlRouter(object):
    """ url = path/path/path/
        self.routers = {
            "": view,
            'api', {
                'news': view,
                '(?P<>)':
            }
        ]

    """
    def __init__(self, urls, patterns="urlpatterns"):
        self.routers = {}
        if isinstance(urls, str):
            urls = import_string(f"{urls}.{patterns}")

        for para in urls:
            if len(para) == 2:
                self.add_path(para[0], para[1])
            else:
                self.add_path(para[0], para[1], para[2])

    def pop_path(self, url):
        res = ""
        i = 0
        for x in url:
            if x == '/':
                return res, url[i+1:]
            else:
                res += x
                i += 1
        return res, ''

    @classmethod
    def update_router(cls, router, router_added):
        for k, v in router_added.items():
            if k in router:
                cls.update_router(router[k], v)
            else:
                router[k] = v

    def add_path(self, url, view, para=None):
        router = self.routers
        url = url.strip('/')

        while url:
            path, url = self.pop_path(url)
            if path not in router:
                router[path] = dict()
            router = router[path]

        if isinstance(view, self.__class__):
            self.update_router(router, view.routers)
        else:
            if not inspect.iscoroutinefunction(view):
                view = functools.partial(sync_to_async, view)
            router[""] = view, para

    @classmethod
    def match_url(cls, routers, url):
        # 正则匹配 router
        for path in routers:
            match = re.match("{}$".format(path), url)
            if match:
                return routers[path], match.groupdict()
        return {}, {}

    def get_url_view(self, url):
        # 获取url对应的view函数
        url = url.strip('/')
        routers = self.routers
        kwargs = {}

        while url:
            path, url = self.pop_path(url)
            if path in routers:
                # 直接找到
                routers = routers[path]
                continue

            # 最大匹配
            _url = '{}/{}'.format(path, url).strip('/')
            res, _kwargs = self.match_url(routers, _url)
            if res:
                kwargs.update(_kwargs)
                routers = res
                url = ""
                continue

            # 局部匹配
            res, _kwargs = self.match_url(routers, path)
            if res:
                kwargs.update(_kwargs)
                routers = res
                continue

            # 404
            routers = {}

        view, para = routers.get(url, (None, None))
        if para:
            kwargs.update(para)

        return view, kwargs


include = UrlRouter
