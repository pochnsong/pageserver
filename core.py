import importlib
from .router import UrlRouter
from .conf import settings
from .http.response import Http404


class PageApp(object):
    http_request_middlewares = []
    http_response_middlewares = []

    ws_receive_middlewares = [] #todo
    ws_send_middlewares = []

    def load_middlewares(self):
        """加载中间件"""
        def load():
            _mods = path.split(".")
            _package_name = ".".join(_mods[:-1])
            _package = importlib.import_module(_package_name)
            return getattr(_package, _mods[-1])()

        for x in [('http', 'request', 'response'), ('ws', 'receive', 'send')]:
            for path in getattr(settings, f'{x[0].upper()}_MIDDLEWARE'):
                handle = load()
                if hasattr(handle, f'{x[1]}_handle'):
                    getattr(self, f'{x[0]}_{x[1]}_middlewares').append(handle)
                if hasattr(handle, f'{x[2]}_handle'):
                    getattr(self, f'{x[0]}_{x[2]}_middlewares').append(handle)

    def __init__(self, custom_settings=None):
        self.settings = custom_settings
        self.router = None

    async def setup(self):
        await settings.setup(self.settings)

        urls = importlib.import_module(settings.URLS)
        routers = getattr(urls, 'urlpatterns', [])

        if settings.ADMIN:
            settings.HTTP_MIDDLEWARE.append("pageserver.sites.admin.middleware.TokenMiddleware")
            routers.append((settings.ADMIN['urls'], UrlRouter("pageserver.sites.admin.urls")))

        self.load_middlewares()
        self.router = UrlRouter(routers)

    async def http_process(self, request):
        view, kwargs = self.router.get_url_view(request.path)
        if callable(view):
            for handle in self.http_request_middlewares:
                handle.request_handle(request)

            response = await view(request, **kwargs)

            for handle in self.http_response_middlewares:
                handle.response_handle(request, response)

            return response

        return Http404()

    async def ws_process(self, request, reader, writer):
        try:
            view, kwargs = self.router.get_url_view(request.path)
            if callable(view):
                await view(request, reader, writer, **kwargs)
        except ConnectionResetError:
            pass
