from pageserver.http.response import Http405
from pageserver.views.base import *
from pageserver.db.query import Q
from pageserver.http.response import HttpResponse, JsonResponse
from pageserver.http.exception import Error
from pageserver.db.fields import *
from pageserver.db.models import ModelChangeEvents
from pageserver.cache import cache
from pageserver.utils import log, asynctools
from pageserver.utils.asynctools import sync_to_async
from pageserver.utils.log import error
import copy
import inspect
import asyncio
import functools
import os


class TemplateView(View):
    _template = None
    use_cache = False
    template_name = None

    def get_template_name(self):
        return os.path.join(settings.TEMPLATE_DIR, self.template_name)

    async def get_template(self):
        cls = self.__class__
        if cls._template:
            return cls._template

        html = await asynctools.file(self.get_template_name(), mode='rb')
        if self.use_cache:
            cls._template = html

        return html

    async def get(self, request, **kwargs):
        response = self.get_template()
        if inspect.isawaitable(response):
            response = await response
        return HttpResponse(body=response)



class API(View):
    use_thread = False
    cors_origin = "*" # "*"
    cors_header = "Content-Type"

    def check_perm(self):
        return True

    async def options(self, request):
        response = HttpResponse()
        response.header["Access-Control-Allow-Origin"] = self.cors_origin
        response.header["Access-Control-Allow-Headers"] = request.META['access-control-request-headers']
        return response

    @classmethod
    async def as_view(cls, request, **kwargs):
        view = cls(request)
        http_method = request.method.lower()

        func = getattr(view, http_method, None)

        if not func:
            return Http405()

        if http_method != "options" and not bool(view.check_perm()):
            return Http405()

        if not inspect.iscoroutinefunction(func):
            if view.use_thread:
                func = functools.partial(asyncio.to_thread, func)
            else:
                func = functools.partial(sync_to_async, func)

        try:
            response = await func(request, **kwargs)
            if isinstance(response, dict):
                response = JsonResponse(response)
        except Error as e:
            response = JsonResponse({'status': 'FAIL', 'errors': str(e)})
        except Exception as e:
            error(e)
            response = JsonResponse({'status': 'FAIL', 'errors': 500})

        if view.cors_origin:
            response.header["Access-Control-Allow-Origin"] = view.cors_origin
            # response.header["Access-Control-Allow-Headers"] = request.META['access-control-request-headers']
        return response


class AdminAPI(API):
    model_class = None
    fields = "__all__"
    with_meta = True
    limit = 20

    def check_perm(self):
        return False

    def get_filters(self):
        return {}

    def get_model_class(self):
        return self.model_class

    def get_form_data(self, model_class):
        res = {}
        for field_name, field in model_class._meta['fields'].items():

            if field_name not in self.request.POST:
                continue

            value = self.request.POST[field_name]

            if isinstance(field, (IntegerField, FloatField)):
                if value in ['null', '']:
                    value = None

            if value is None:
                if not field.attrs['nullable']:
                    raise Exception("{} not nullable".format(field_name))
            else:
                value = field.to_python(value)

            res[field_name] = value

        return res

    @classmethod
    def get_fields(cls, model_class):
        return tuple(model_class._meta['fields'])

    def get_skip_limit(self):
        skip = abs(int(self.request.GET.get('skip', 0)))
        limit = self.request.GET.get('limit', self.limit)
        limit = "all" if limit == 'all' else abs(int(limit))

        if isinstance(self.limit, int):
            limit = min(limit, self.limit)
        return skip, limit

    def get_ordering(self, columns):
        res = []
        if order_by := self.request.GET.get('order_by'):
            for v in order_by.split(','):
                if v in columns:
                    res.append(v)

        return res

    def get_queryset(self, model_class, columns):
        skip, limit = self.get_skip_limit()

        q = self.get_filters()
        if isinstance(q, dict):
            q = Q(**q)

        queryset = model_class.query(q) \
            .select(columns) \
            .skip(skip).limit(limit) \
            .ordering(*self.get_ordering(columns=columns))

        return queryset

    def get(self, request):

        try:
            model_class = self.get_model_class()
            columns = self.get_fields(model_class)
            queryset = self.get_queryset(model_class, columns)
            dataset = queryset.all(to='list')

            res = {'status': 'OK', 'object_list': dataset}

            if queryset._offset == 0:
                res['count'] = queryset.count()

                if self.with_meta:
                    fields = []
                    for name in columns:
                        field = model_class._meta['fields'][name]
                        attrs = {}
                        for _k, _v in field.attrs.items():
                            if callable(_v):
                                _v = _v()
                            attrs[_k] = _v
                        attrs['name'] = name
                        fields.append(attrs)

                    res['fields'] = fields

            return res

        except Exception as e:
            log.error(e)
            return {'status': 'FAIL', 'errors': str(e)}


    def post(self, request):
        try:
            model_class = self.get_model_class()
            form_data = self.get_form_data(model_class)
            primary_key = model_class._meta['primary_key']
            pk = form_data.get(primary_key)
            action = request.GET['action']

            if action == 'edit':
                obj = model_class.query(**{primary_key: pk}).one()
            elif action == 'new':
                obj = model_class()
            else:
                return {'status': 'FAIL', 'errors': 'unknown action'}

            for k, f in model_class._meta['fields'].items():
                if k in form_data:
                    setattr(obj, k, form_data[k])

                    if isinstance(f, FileField) and k in request.FILES:
                        setattr(obj, k, request.FILES[k][0])

            obj.save()
            return {'status': 'OK', 'object': getattr(obj, primary_key)}
        except Exception as e:
            log.error(e)
            return {'status': 'FAIL', 'errors': str(e)}

    def delete(self, request):
        model_class = self.get_model_class()
        primary_key = model_class._meta['primary_key']
        pk = request.GET.get('pk')
        try:
            obj = model_class.query(**{primary_key: pk}).limit(1).one()
            obj.delete()
        except Exception as e:
            return {'status': 'FAIL', 'errors': '无法删除'}
        return {'status': 'OK'}


class ListAPI(API):
    model_class = None
    fields = "__all__"
    exclude = []  # 排除的字段
    limit = 100
    filters = []
    order_by = []
    joins = []
    data_format = "dict"  # dict|list

    def check_perm(self):
        return False

    def get_filters(self):
        res = {}
        for k in self.filters:
            if k in self.request.GET:
                res[k] = self.request.GET[k]

        return res

    def get_skip_limit(self):
        skip = abs(int(self.request.GET.get('skip', 0)))
        limit = self.request.GET.get('limit', self.limit)
        limit = "all" if limit == 'all' else abs(int(limit))

        if isinstance(self.limit, int):
            limit = min(limit, self.limit)
        return skip, limit

    def get_ordering(self):
        res = []
        if 'order_by' in self.request.GET:
            for v in self.request.GET['order_by'].split(','):
                key = v[1:] if v.startswith('-') else v
                if key in self.order_by:
                    res.append(v)

        return res


    def get_fields(self):
        all_fields = tuple(self.model_class._meta['fields'])

        if self.fields == '__all__':
            _res = copy.copy(all_fields)
        else:
            _res = copy.copy(self.fields)

        res = []
        i = 0
        self.pk = -1
        for k in _res:
            if k not in self.exclude:
                res.append(k)
                if k == self.model_class._meta['primary_key']:
                    self.pk = i
                i += 1
        return res

    def get_joins(self):
        return self.joins

    def get_object_list(self, queryset):
        return queryset.all(to=self.data_format)

    def get_queryset(self):
        skip, limit = self.get_skip_limit()

        q = self.get_filters()
        if isinstance(q, dict):
            q = Q(**q)

        queryset = self.model_class.query(q) \
            .select(self.get_fields()) \
            .skip(skip).limit(limit) \
            .ordering(*self.get_ordering())

        for j in self.get_joins():
            queryset.join(**j)

        return queryset

    def get(self, request):
        queryset = self.get_queryset()
        dataset = self.get_object_list(queryset)

        res = {'status': 'OK', 'object_list': dataset}

        if hasattr(self, 'get_extra'):
            res['extra'] = getattr(self, 'get_extra')()

        if queryset._offset == 0:
            if self.data_format == 'list':
                res['columns'] = queryset.columns(split="$")

            if queryset._limit:
                res['count'] = queryset.count()

        return res


class ALLAPI(API):
    model_class = None
    fields = "__all__"
    exclude = []  # 排除的字段
    joins = []
    cache_key = None
    timeout = 3600
    _cache_keys = []

    def check_perm(self):
        return False

    def get_fields(self):
        all_fields = tuple(self.model_class._meta['fields'])

        if self.fields == '__all__':
            _res = copy.copy(all_fields)
        else:
            _res = copy.copy(self.fields)

        res = []
        for k in _res:
            if k not in self.exclude:
                res.append(k)
        return res

    def get_joins(self):
        return self.joins

    def get_filters(self):
        return {}

    def get_queryset(self):

        q = self.get_filters()
        if isinstance(q, dict):
            q = Q(**q)

        queryset = self.model_class.query(q) \
            .select(self.get_fields()) \

        for j in self.get_joins():
            queryset.join(**j)

        return queryset

    @classmethod
    def clean_handle(cls, **kwargs):
        for ckey in cls._cache_keys:
            cache.delete(ckey)

    def get_cache_key(self):
        key = self.cache_key
        if key:
            q = Q(**self.get_filters())
            if q:
                key += f"@{q}"
        return key

    def get(self, request):
        try:
            ckey = self.get_cache_key()
            res = None
            if ckey:
                res = cache.get(ckey)

            if res is None:
                queryset = self.get_queryset()
                dataset = queryset.all(to='list')

                res = {
                    'status': 'OK',
                    'dataset': dataset,
                    'columns': queryset.columns(split="$"),
                }

                if hasattr(self, 'get_extra'):
                    res['extra'] = getattr(self, 'get_extra')()

                if ckey:
                    cls = self.__class__
                    if ckey not in cls._cache_keys:
                        cls._cache_keys.append(ckey)
                    cache.set(ckey, value=res, timeout=self.timeout)
                    ModelChangeEvents.append(self.model_class, cls.clean_handle, ckey)

            return res

        except Exception as e:
            return JsonResponse({'status': 'FAIL', 'errors': 500})


__all__ = [
    "TemplateView",
    "API",
    "AdminAPI",
    "ListAPI",
    "ALLAPI",
    "Error",
]
