from pageserver.db.fields import *
from pageserver.db import database
from pageserver.db.query import Query
from pageserver.http.exception import Error
from pageserver.utils import image
from pageserver.conf import settings
import os
from multiprocessing import Process
import re


class ModelChangeEvents:
    """
    注册模型事件，
    _handles = {
        'model1_hash': [ func1, func2, ...]
    }
    _names = {
        'model1_hash': [func1_name, func2_name, ...]
    }
    +v1,0 post_save保存后事件
    """
    _handles = {}
    _names = {}

    @classmethod
    def append(cls, model_class, func, handle_name=None):
        """
        注册数据变更事件,
        """
        m_key = hash(model_class)
        _name = handle_name or hash(func)
        h_name = f"{m_key}@{_name}"

        if m_key not in cls._names:
            cls._names[m_key] = []
            cls._handles[m_key] = []

        if h_name in cls._names[m_key]:
            return

        cls._handles[m_key].append(func)
        cls._names[m_key].append(h_name)


    @classmethod
    def remove(cls, model_class, handle, handle_name=None):
        m_key = hash(model_class)
        _name = handle_name or hash(handle)
        h_name = f"{m_key}@{_name}"

        if m_key not in cls._names:
            return

        if h_name not in cls._names[m_key]:
            return

        try:
            find = cls._names[m_key].index(h_name)
            del cls._names[find]
            del cls._handles[find]
        except Exception as e:
            import traceback
            traceback.print_exc()
            pass

    @classmethod
    def clean(cls, model_class):
        m_key = hash(model_class)
        if m_key in cls._names:
            cls._handles[m_key].clear()
            cls._names[m_key].clear()

    @classmethod
    def events(cls, model_class):
        m_key = hash(model_class)
        return cls._handles.get(m_key, [])


class ModelBase(type):

    def __new__(mcs, class_name, bases, attrs):
        meta = {
            'db_table': class_name.lower(),
            'label': class_name,
            'fields': {},
            'use_db': 'default',
            'primary_key': None,
        }
        _attrs = {}

        _meta = {}

        for key, val in attrs.items():
            if key == "meta":
                _meta = val
            elif isinstance(val, Field):
                meta["fields"][key] = val
                if val.attrs["primary_key"]:
                    meta["primary_key"] = key
            else:
                _attrs[key] = val

        meta.update(_meta)
        _attrs["_meta"] = meta
        return super().__new__(mcs, class_name, bases, _attrs)


class Model(metaclass=ModelBase):
    #
    # meta = {
    #    'db_table': 'device',
    #    'label': '设备',
    #    'unique_together': ""
    # }
    #

    @classmethod
    def load(cls, **kwargs):
        """数据库载入"""
        obj = cls()
        for k, v in kwargs.items():
            field = cls._meta['fields'].get(k)
            if v is not None:
                v = field.to_python(v)
            setattr(obj, k, v)
        return obj

    def __init__(self, **kwargs):
        self.instance = None

        for k, field in self._meta['fields'].items():
            default = field.attrs["default"]
            v = default() if callable(default) else default
            setattr(self, k, v)

        for k, v in kwargs.items():
            setattr(self, k, v)

    def to_dict(self, fields="all"):
        res = {}
        if fields == "all":
            fields = self._meta['fields']

        for k in fields:
            res[k] = getattr(self, k)
        return res

    @classmethod
    def query(cls, *args, **kwargs):
        use_db = cls._meta['use_db']
        query = Query(db=database[use_db], model_class=cls).query(*args, **kwargs)
        return query

    def pre_save(self):
        # 验证数据
        for name, field in self._meta['fields'].items():
            value = field.to_database(getattr(self, name), instance=self)
            # 空
            if not field.attrs['nullable'] and value is None:
                raise Exception(f"{name} is not nullable")

            if check := field.attrs.get('re'):
                if not re.match(check, str(value)):
                    raise Error(f"bad {name}")

            if 'choice' in field.attrs:
                if value not in [o[0] for o in field.attrs['choice']]:
                    raise Error(f"{name} value not in choice")

            setattr(self, name, value)

    def _post_save(self):

        for name, field in self._meta['fields'].items():
            if not isinstance(field, ImageField):
                continue

            if max_size := field.attrs.get('max_size'):
                if value := getattr(self, name):
                    Process(
                        target=image.resize,
                        args=(os.path.join(settings.MEDIA_DIR, value), max_size, field.attrs.get('image_format', None))
                    ).start()
                    pass
        pass

    def post_save(self):
        pass

    def save(self, use_db=None, conn=None, fields="__all__"):
        """
        fields = update 有效
        """
        self.pre_save()
        if use_db is None:
            use_db = self._meta['use_db']
        if self.instance is None:
            method = 'insert'
            database[use_db].insert(self, conn)
        else:
            method = 'update'
            database[use_db].update(self, conn, fields)

        try:
            self._post_save()
            self.post_save()
        except Error as e:
            pass

        for fn in ModelChangeEvents.events(self.__class__):
            try:
                fn(method=method, instance=self)
            except:
                import traceback
                traceback.print_exc()
                pass
        return self

    def delete(self, use_db="default", conn=None):
        if self.instance is not None:
            pk = self._meta['primary_key']
            self.query(**{pk: self.instance}).use_conn(conn).delete()
            self.instance = None
            for fn in ModelChangeEvents.events(self.__class__):
                try:
                    fn(method='delete', instance=self)
                except:
                    pass
