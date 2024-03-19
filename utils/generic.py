from pageserver.cache import cache
from pageserver.db.models import ModelChangeEvents

__all__ = ["get_obj"]

def clean_obj_cache(**kwargs):
    obj = kwargs['instance']
    _key = f"{obj.__class__.__name__}@{obj.instance}"
    cache.delete(_key)


def get_obj(model_class, obj_id, *, fields: list = "__all__", fields_exclude: list = None, clean: bool = False):
    _key = f"{model_class.__name__}@{obj_id}"
    if clean:
        cache.delete(_key)
        return

    _data = cache.get(_key)
    if _data is None:
        ModelChangeEvents.append(model_class, clean_obj_cache)
        fields_allowed = model_class._meta["fields"]
        _select = []
        if fields == "__all__":
            fields = fields_allowed.keys()
        if fields_exclude is None:
            fields_exclude = []

        if not fields_allowed:
            fields_exclude = []

        for k in fields:
            if k in fields_allowed and k not in fields_exclude:
                _select.append(k)

        obj = model_class.query(id=obj_id).select(_select).one()
        if obj is None:
            return None
        _data = obj.to_dict()
        cache.set(_key, _data, 600)

    return model_class(**_data)
