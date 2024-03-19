import json
from datetime import datetime, date
import copy


def data_decode(obj):
    if '@datetime' in obj:
        obj = datetime.strptime(obj['_'], "%Y%m%dT%H:%M:%S.%f")
    elif '@date' in obj:
        obj = datetime.strptime(obj['_'], "%Y%m%d").date()
    return obj


def data_encode(obj):
    if isinstance(obj, datetime):
        obj = {'@datetime': True, '_': obj.strftime("%Y%m%dT%H:%M:%S.%f")}
    elif isinstance(obj, date):
        obj = {'@date': True, '_': obj.strftime("%Y%m%d")}
    return obj


class Wrapper:

    @classmethod
    def serialize(cls, value):
        return json.dumps(value, ensure_ascii=False, default=data_encode)

    @classmethod
    def deserialize(cls, value):
        return json.loads(value, object_hook=data_decode)
