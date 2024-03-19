from .sql import SQL
from pageserver.db.function import *
import string

__all__ = ["Helper"]
class Fmt:
    @classmethod
    def _where_sql(cls, where, joins=()):
        if not where:
            return "", []

        _sql = []
        paras = []

        for x in where:
            if isinstance(x, str):
                _sql.append(x)
                continue

            k, o, v = x
            if "." in k:
                _k = k.split('.', 1)
                checked = False
                for join in joins:
                    if join.join_as == _k[0]:
                        checked = True
                        break
                if not checked:
                    raise Exception('unknown table by where {}'.format(k))

                k = "{}.`{}`".format(_k[0], _k[1])

            else:
                if joins:
                    k = "a.`{}`".format(k)
                else:
                    k = "`{}`".format(k)

            if o == '=' and v in [None, 'null', 'NULL']:
                _sql.append("{} is NULL".format(k))
                continue

            if o == '!=' and v in [None, 'null', 'NULL']:
                _sql.append("{} is not NULL".format(k))
                continue

            if o == "in":
                _sql.append("{}{}({})".format(k, o, ", ".join(["?"] * len(v))))
                paras += v
            else:
                _sql.append("{}{}?".format(k, o))
                paras.append(v)
        return " WHERE {}".format("".join(_sql)), paras

    @classmethod
    def _column_str(cls, x, join_as=None):
        """
        return `id` | b.`id`
        """
        _as = ""
        if join_as:
            _as = f"{join_as}."
        return f"{_as}`{x}`" if isinstance(x, str) else x.str()

    @classmethod
    def _columns_str(cls, columns, _as=""):
        return ",".join([cls._column_str(x, _as) for x in columns])

    @classmethod
    def _from_sql(cls, model_class, columns, joins=()):
        db_table = model_class._meta['db_table']
        if not joins:
            return f"`{db_table}`", ",".join([cls._column_str(x) for x in columns]), ""

        _form = [f"`{db_table}` a"]
        _columns = [cls._column_str(x, 'a') for x in columns]

        for i, _join in enumerate(joins):
            _as = _join.join_as
            _form.append("{} JOIN `{}` {} ON a.`{}`={}.`{}`".format(
                _join.join_type, _join.model_class._meta['db_table'], _as, _join.field, _as, _join.link_field))

            if _join.columns:
                _columns += [cls._column_str(x, _as) for x in _join.columns]

        return " ".join(_form), ",".join(_columns), "a"


class Helper(object):

    @classmethod
    def create_table(cls, model_class, table_name=None):
        if table_name is None:
            table_name = model_class._meta['db_table']
        fields = []
        for field_name in model_class._meta['fields']:
            field = model_class._meta['fields'][field_name]
            fields.append(f"`{field_name}` {SQL.field(field)}")
        columns = ",".join(fields)
        unique_together = ""
        if _columns := model_class._meta.get("unique_together"):
            unique_together = f", UNIQUE ({','.join(_columns)}) ON CONFLICT ROLLBACK"
        sql_str = f"CREATE TABLE `{table_name}`({columns} {unique_together})"
        return [(sql_str, None)]

    @classmethod
    def rebuild_table(cls, model_class, select_str):
        """
        重建数据表
        编码时sqlite无法直接变更约束，因此采取的方案为新建table，复制数据后后改名
        """
        table_name = model_class._meta['db_table']
        _tmp_table_name = f"_tmp_{table_name}"

        commands = cls.create_table(model_class, table_name=_tmp_table_name)+[
            #("BEGIN TRANSACTION", None),
            (f"INSERT INTO `{_tmp_table_name}` ({select_str}) SELECT {select_str} FROM {table_name}", None),
            (f"DROP TABLE `{table_name}`", None),
            (f"ALTER TABLE `{_tmp_table_name}` RENAME TO `{table_name}`", None),
            #("COMMIT", None)
        ]
        return commands

    @classmethod
    def drop_table(cls, model_class):
        sql_str = f"DROP TABLE IF EXISTS `{model_class._meta['db_table']}`"
        return [(sql_str, None)]

    @classmethod
    def alter_add(cls, model_class, field_name, field):
        """增加字段"""
        table_name = model_class._meta['db_table']
        sql_str = "ALTER TABLE `{}` ADD `{}` {}".format(
            table_name, field_name, SQL.field(field))

        default = field.attrs['default']

        #if default is not None:
        #    sql_str += " DEFAULT {}".format(default)
        return [(sql_str, None)]

    @classmethod
    def alter_drop(cls, model_class, field_name):
        """删除字段"""
        field_str = []
        for _name in model_class._meta['fields']:
            if _name == field_name:
                continue
            field_str.append("`{}`".format(_name))

        select_str = ",".join(field_str)
        return cls.rebuild_table(model_class, select_str=select_str)

    @classmethod
    def alter_change(cls, model_class, old_name, new_name, field):
        """变更字段"""
        table_name = model_class._meta['db_table']
        sql_str = "ALTER TABLE `{}` RENAME COLUMN `{}` TO `{}`".format(
            table_name, old_name, new_name)
        return [(sql_str, None)]

    @classmethod
    def alter_modify(cls, model_class, field_name, field):
        """变更数据类型"""

        field_str = []
        for _name in model_class._meta['fields']:
            field_str.append(f"`{_name}`")

        select_str = ",".join(field_str)
        return cls.rebuild_table(model_class, select_str)

    @classmethod
    def alter_constraint(cls, model_class, field_name, constraint):
        """变更约束"""
        table_name = model_class._meta['db_table']
        sql = None
        if constraint['k'] == 'unique':
            if constraint['v']:
                sql = f"CREATE UNIQUE INDEX `uni_{table_name}_{field_name}` ON `{table_name}`(`{field_name}`)"
            else:
                sql = f"DROP INDEX `uni_{table_name}_{field_name}`"
        return [(sql, None)]

    @classmethod
    def insert(cls, obj):
        keys = []
        values = []
        for k in obj._meta['fields']:
            keys.append('`{}`'.format(k))
            values.append(getattr(obj, k))

        sql = "INSERT INTO `{}` ({}) VALUES ({})".format(obj._meta['db_table'], ", ".join(keys), ", ".join(["?"]*len(keys)))
        return [(sql, tuple(values))]

    @classmethod
    def update(cls, obj, fields):
        keys = []
        values = []
        for k in obj._meta['fields']:
            keys.append('`{}`'.format(k))
            values.append(getattr(obj, k))

        primary_key = obj._meta['primary_key']
        sql = "UPDATE {} SET {} WHERE `{}`=?".format(
            obj._meta['db_table'],
            ", ".join(["{}=?".format(k) for k in keys]),
            primary_key,
        )
        values.append(getattr(obj, primary_key))
        return [(sql, tuple(values))]




    @classmethod
    def select(cls, model_class, columns,
               where=None, skip=None, limit=None,
               **kwargs):
        """
        where
        order_by = [(column, asc),]
        """
        orders = kwargs.get('order_by', '')
        joins = kwargs.get('joins', ())
        group_by = kwargs.get('group_by', ())

        _form, _columns, _as = Fmt._from_sql(model_class, columns, joins=joins)

        sql = f"SELECT {_columns} FROM {_form}"
        _where_sql, paras = Fmt._where_sql(where, joins=joins)

        sql += _where_sql
        if group_by:
            sql += f" GROUP BY {Fmt._columns_str(group_by, _as)}"

        if orders:
            _orders = []
            for f, d in orders:
                if _as:
                    _orders.append(f"`{_as}`.`{f}` {d}")
                else:
                    _orders.append(f"`{f}` {d}")
            sql += " ORDER BY {}".format(",".join(_orders))

        if skip and not limit:
            limit = 100

        if limit:
            sql += f" LIMIT {int(limit)}"

        if skip:
            sql += f" OFFSET {int(skip)}"

        #sql += " FOR UPDATE" if lock else ""

        return [(sql, tuple(paras))]

    @classmethod
    def delete(cls, model_class, where):
        """
        where
        order_by = [(column, asc),]
        """
        sql = f"DELETE FROM `{model_class._meta['db_table']}`"

        _where_sql, paras = Fmt._where_sql(where)

        sql += _where_sql

        return [(sql, tuple(paras))]

    @classmethod
    def get_index_name(cls, prefix, columns):
        columns = list(columns)
        columns.sort()
        return "{}_{}".format(prefix, "_".join(columns))

    @classmethod
    def unique_add(cls, model_class, columns=None):
        """
        添加约束
        编码时sqlite无法直接变更约束，因此采取的方案为新建table，复制数据后后改名
        """
        field_str = []
        for _name in model_class._meta['fields']:
            field_str.append(f"`{_name}`")

        select_str = ",".join(field_str)
        return cls.rebuild_table(model_class, select_str), cls.get_index_name("uni", columns)


    @classmethod
    def unique_drop(cls, model_class, index_name):
        """
        删除约束
        编码时sqlite无法直接变更约束，因此采取的方案为新建table，复制数据后后改名
        """
        field_str = []
        for _name in model_class._meta['fields']:
            field_str.append(f"`{_name}`")

        select_str = ",".join(field_str)
        return cls.rebuild_table(model_class, select_str)
