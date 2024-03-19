import copy

class QueryDict(dict):

    def __getitem__(self, key):
        v = super().__getitem__(key)
        if isinstance(v, list):
            return v[-1]
        return v

    def get(self, key, default=None):
        try:
            val = self[key]
        except KeyError:
            return default
        if not val:
            return default
        return val

    def getlist(self, key, default=None):
        try:
            v = super().__getitem__(key)
            if isinstance(v, list):
                return v
            if not v:
                return []
            return [v, ]
        except KeyError:
            return []

    def copy(self):
        return copy.deepcopy(self)
