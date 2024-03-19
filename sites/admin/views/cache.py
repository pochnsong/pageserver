from pageserver.views.generic import *
from pageserver.http.exception import Error
from pageserver.cache import cache
from pageserver.conf import settings
from .account import check_perm


class CacheDBAPI(API):
    def check_perm(self):
        return check_perm(self.request)

    def get(self, request):
        return {'status': 'OK', 'result': list(settings.CACHE.keys())}


class CacheKeysAPI(API):
    def check_perm(self):
        return check_perm(self.request)

    def get(self, request):
        alias = request.GET.get("db", "default")
        skip = int(request.GET.get('cursor', 0))
        next_skip, result = cache.keys(cursor=skip, alias=alias)
        res = {'status': 'OK', 'keys': result, 'cursor': next_skip}
        if next_skip == 0:
            res['size'] = cache.size(alias=alias)

        return res


class CacheValueAPI(API):
    def check_perm(self):
        return check_perm(self.request)

    def get(self, request):
        alias = request.GET["db"]
        k = request.GET['key']
        _t = cache.get_type(k, alias=alias)
        value = "-"
        if _t == 'string':
            value = cache.get(k, alias=alias)
        if _t == 'list':
            value = cache.list_get(k, alias=alias)
        if _t == 'hash':
            value = cache.get(k, alias=alias)

        return {'status': 'OK', 'value': value, 'type': _t, 'ttl': cache.ttl(k, alias=alias)}


class CacheDeleteAPI(API):
    def check_perm(self):
        return check_perm(self.request)

    def post(self, request):
        try:
            alias = request.POST["db"]
            k = request.POST['key']
            cache.delete(k, alias=alias)
            return {'status': 'OK'}
        except Exception as e:
            return {'status': 'FAIL', 'errors': str(e)}

