from pageserver.conf import settings
import types
import os
import json
import time
import uuid
from datetime import datetime


class Field(object):
    field_type = "field"

    def __init__(self, nullable=True, default=None, primary_key=False, unique=False, index=False, **attrs):
        attrs.update({
            "default": default,
            "nullable": nullable,
            "unique": unique,
            "index": index,
            "primary_key": primary_key,
            "type": self.field_type,
        })
        self.attrs = attrs

    def to_database(self, val, **kwargs):
        """保存到数据库时调用，一般转换成字符串,或数字"""
        return val

    def to_python(self, val):
        """转换成python对象时调用"""
        return val


class VarCharField(Field):
    field_type = "char"

    def __init__(self, max_length, default="", **kwargs):
        super().__init__(max_length=max_length, default=default, **kwargs)

    def to_database(self, val, **kwargs):
        return str(val)

    def to_python(self, val):
        return str(val)


class CharField(Field):
    field_type = "char"

    def __init__(self, max_length, default="", **kwargs):
        super().__init__(max_length=max_length, default=default, **kwargs)

    def to_database(self, val, **kwargs):
        return str(val)

    def to_python(self, val):
        return str(val)


class TextField(Field):
    field_type = "text"

    def __init__(self, max_length=None, default="", **kwargs):
        super().__init__(max_length=max_length, default=default, **kwargs)

    def to_database(self, val, **kwargs):
        return str(val)

    def to_python(self, val):
        return str(val)


class JsonField(TextField):

    def __init__(self, default=None, **kwargs):
        if 'max_length' in kwargs:
            del kwargs['max_length']
        super().__init__(max_length=None, default=default, **kwargs)

    def to_database(self, val, **kwargs):
        if val in ['', None]:
            return val

        if isinstance(val, str):
            val = json.loads(val)
        try:
            val = json.dumps(val, ensure_ascii=False)
        except:
            raise Exception(f'the value({val}) can\'t dumps with json')
        return val

    def to_python(self, val):
        if val in ['', None]:
            return val

        if isinstance(val, str):
            return json.loads(val)
        return val


class FileField(TextField):
    field_type = "file"

    def __init__(self, upload_to="", **kwargs):
        kwargs.update({
            'upload_to': upload_to,
            'max_length': None,
            'default': '',
        })
        super().__init__(**kwargs)

    def to_database(self, val, **kwargs):
        if not val:
            return ''

        if not isinstance(val, str):
            upload_to = self.attrs['upload_to']
            if isinstance(upload_to, str):
                upload_to = datetime.now().strftime(upload_to)
                
            if callable(upload_to):
                upload_to = upload_to(**kwargs)

            if upload_to is None:
                return None

            save_dir = os.path.join(settings.MEDIA_DIR, upload_to)
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)

            filename = getattr(val, "filename", f"{time.time()}.")
            suffix = filename.split('.')[-1]
            save_as = os.path.join(save_dir, filename)

            i = 0
            while True:
                i += 1
                if not os.path.exists(save_as):
                    break

                if i > 50:
                    raise Exception("filename errors")

                filename = f"{uuid.uuid1().hex}.{suffix}"
                save_as = os.path.join(save_dir, filename)

            with open(save_as, 'wb') as wf:
                wf.write(val.read())

            return f"{upload_to}/{filename}"

        return val


class ImageField(FileField):
    field_type = "image"


class IntegerField(Field):
    field_type = "int"

    def to_database(self, val, **kwargs):
        if val in [None, '', 'null', 'undefined', 'None']:
            return None
        return int(val)

    def to_python(self, val):
        return int(val)

class TinyIntField(IntegerField):
    field_type = "int"
    pass


class BigIntegerField(IntegerField):
    field_type = "char"


class TimestampField(IntegerField):
    field_type = "timestamp"


class BigTimestampField(BigIntegerField):
    field_type = "timestamp"


class DateField(Field):
    field_type = "date"

    def to_database(self, val, **kwargs):
        return val

    def to_python(self, val):
        if isinstance(val, str):
            val = datetime.strptime(val, "%Y-%m-%d").date()
        return val


class DateTimeField(Field):
    field_type = "datetime"

    def to_database(self, val, **kwargs):
        return val

    def to_python(self, val):
        return str(val)

class AutoField(IntegerField):
    field_type = "auto"

    def __init__(self, **kwargs):
        kwargs.update({
            "auto_increment": True,
            "primary_key": True,
        })
        super().__init__(**kwargs)


class BigAutoField(BigIntegerField):

    field_type = "auto"

    def __init__(self, **kwargs):
        kwargs.update({
            "auto_increment": True,
            "primary_key": True,
        })
        super().__init__(**kwargs)


class FloatField(Field):
    field_type = "float"

    def to_database(self, val, **kwargs):
        return float(val)

    def to_python(self, val):
        return float(val)


class DoubleField(FloatField):
    field_type = "float"


class BoolField(Field):
    field_type = "bool"

    def to_database(self, val, **kwargs):
        if val in ['true', 'True', '1']:
            return True

        if val in ['false', 'False', '0']:
            return False

        return bool(val)

    def to_python(self, val):
        return bool(val)
