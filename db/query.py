import re
from .function import *

OP = {
    'gt': '>',
    'gte': '>=',
    'lt': '<',
    'lte': '<=',
    'nt': '!=',
    'in': 'in',
    'like': ' like ',
    'endswith': ' like ',
    'startswith': ' like ',
}

def to_str(v):
    res = ""
    for x in v:
        res += str(x)
    return res

class Q(object):
    def __init__(self, **kwargs):
        self.where = []
        _with_and = False
        for k, v in kwargs.items():
            if _with_and:
                self.where.append(" AND ")

            ks = k.split('__')
            if len(ks) == 1:
                op = "="
            else:
                op = OP[ks[1]]
                if ks[1] == 'like':
                    v = f"%{v}%"
                if ks[1] == 'endswith':
                    v = f"%{v}"
                if ks[1] == 'startswith':
                    v = f"{v}%"

            _with_and = True

            self.where.append([ks[0], op, v])

    def __and__(self, other):
        if not self.where:
            return other

        if not other:
            return self

        res = ['(']
        for x in self.where:
            res.append(x)
        res.append(") AND (")

        for x in other.where:
            res.append(x)

        res.append(")")

        q = Q()
        q.where = res
        return q

    def __or__(self, other):

        if not self.where:
            return other

        if not other:
            return self

        res = ['(']
        for x in self.where:
            res.append(x)

        res.append(") OR (")
        for x in other.where:
            res.append(x)

        res.append(")")
        q = Q()
        q.where = res

        return q

    def __bool__(self):
        return bool(self.where)

    def __unicode__(self):
        return "{}".format(self.where)

    def __str__(self):
        res = ""
        for v in self.where:
            res += to_str(v)
        return res.replace(" ", "_")


class Join(object):
    def __init__(self, field, model_class, link_field, join_type="left", link_name=None, join_as=None, columns=None):
        join_type = join_type.upper()
        if join_type not in ["LEFT", "RIGHT", "FULL", "INNER", ""]:
            raise Exception("unsupported join_type")

        self.join_as = join_as
        self.join_type = join_type
        self.field = field
        self.model_class = model_class
        self.link_field = link_field
        self.link_name = model_class.__name__ if not link_name else str(link_name)
        allowed_fields = list(model_class._meta['fields'])
        # 只允许合法的字段
        if columns is None:
            self.columns = allowed_fields
        else:
            self.columns = []
            for field in columns:
                if field in allowed_fields:
                    self.columns.append(field)


class Query(object):

    def __init__(self, db, model_class):
        self._order_by = ""
        self._offset = None
        self._limit = None
        self._where = Q()
        self._columns = tuple()
        self.model_class = model_class
        self._db = db
        self._conn = None
        self.select("__all__")
        self._join = []
        self.warning = []
        self._group_by = ""

    def use(self, db):
        self._db = db
        return self

    def use_conn(self, conn):
        self._conn = conn
        return self

    def query(self, *args, **kwargs):
        for q in args:
            if isinstance(q, Q):
                self._where = q

        if kwargs:
            self._where = Q(**kwargs)
        return self

    def join(self, field, model_class, link_field="id", join_type="left",
             link_name=None, join_as=None, columns=None):
        """
        Record.query(Q(**{"b.sn": sn})).join("device_id", Device, link_name="device", join_as="b").one()
        field join a.field
        model_class 关联model
        link_field 关联的field
        link_name 关联的名称
        columns 关联表列
        """
        join_as = join_as or chr(98+len(self._join))
        if columns == '__all__':
            columns = model_class._meta['fields'].keys()
        self._join.append(
            Join(
                field, model_class, link_field,
                join_type=join_type, link_name=link_name, join_as=join_as, columns=columns)
        )
        return self

    def select(self, columns: list|str):
        """
            IFNULL(SUM(`{}`), 0) AS `{}`".format(v, k)
        """

        fields = tuple(self.model_class._meta['fields'])
        if columns == "__all__":
            self._columns = fields
            return self

        _columns = []
        for x in columns:
            if isinstance(x, QueryFunction):
                if x.field in fields or x.field == "*":
                    _columns.append(x)
                continue
            if x in fields:
                _columns.append(x)
                continue
            self.warning.append(f'无效的选择字段:{x}')

        self._columns = tuple(_columns)
        return self

    def ordering(self, *args):
        # 'field', '-field'
        if not args:
            return self

        orders = []
        for o in args:
            field, by = o, ""
            if o[0] == "-":
                field, by = o[1:], ' DESC'

            if field in self.model_class._meta["fields"]:
                orders.append((field, by))
            else:
                self.warning.append(f'无效的排序字段:{o}')

        #self._order_by = " ORDER BY {}".format(",".join(orders))
        self._order_by = orders
        return self

    def order_by(self, *args):
        # 'field', '-field'
        if not args:
            return self

        orders = []
        for o in args:
            field, by = o, ""
            if o[0] == "-":
                field, by = o[1:], ' DESC'

            if field in self.model_class._meta["fields"]:
                orders.append((field, by))
            else:
                self.warning.append(f'无效的排序字段:{o}')

        #self._order_by = " ORDER BY {}".format(",".join(orders))
        self._order_by = orders
        return self

    def skip(self, v):
        if v is None:
            self._offset = None
        else:
            self._offset = abs(int(v))
        return self

    def limit(self, v):
        self._limit = None if v in [None, 'all'] else abs(int(v))
        return self

    def all(self, to="model"):
        """
        to: model|dict|row
        """
        #if to == "model":
        #    self.select("__all__")

        return self._db.select(
            self.model_class,
            self._columns, where=self._where.where,
            offset=self._offset, limit=self._limit,
            to=to,
            conn=self._conn,
            order_by=self._order_by,
            group_by=self._group_by,
            joins=self._join,
        )

    def one(self, to="model"):
        self.limit(1)
        res = self.all(to=to)
        return res[0] if res else None

    def count(self):
        _joins = []
        for x in self._join:
            _joins.append(Join(
                x.field, x.model_class, x.link_field,
                join_type=x.join_type, link_name=x.link_name, join_as=x.join_as, columns=[])
            )
        res = self._db.select(
            self.model_class,
            [Count('*')], where=self._where.where,
            offset=self._offset, limit=self._limit,
            to='list',
            conn=self._conn,
            order_by=self._order_by,
            group_by=self._group_by,
            joins=_joins,
        )[0][0]
        return res

    def delete(self):
        return self._db.delete(
            self.model_class,
            self._where.where,
            conn=self._conn,
        )

    def group_by(self, columns):
        self._group_by = columns
        return self

    def columns(self, split="."):
        res = list(self._columns)
        for join in self._join:
            res += [f'{join.link_name}{split}{c}' for c in join.columns]
        return res


__all__ = ["Query", "Sum",  "Count"]
