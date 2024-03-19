from .sql import SQL
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

                k = f"{_k[0]}.`{_k[1]}`"

            else:
                k = f"a.`{k}`" if joins else f"`{k}`"

            if o == '=' and v in [None, 'null', 'NULL']:
                _sql.append(f"{k} is NULL")
                continue

            if o == '!=' and v in [None, 'null', 'NULL']:
                _sql.append(f"{k} is not NULL")
                continue

            if o == "in":
                _sql.append("{}{}({})".format(k, o, ", ".join(["%s"] * len(v))))
                paras += v
            else:
                _sql.append(f"{k}{o}%s")
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
            return f"`{db_table}`", cls._columns_str(columns), ""
        _t = 'a'
        _form = [f"`{db_table}` {_t}"]
        _columns = [cls._columns_str(columns, _t)]

        for i, _join in enumerate(joins):
            _as = _join.join_as
            _form.append(
                f"{_join.join_type} JOIN `{_join.model_class._meta['db_table']}` "
                f"{_as} ON {_t}.`{_join.field}`={_as}.`{_join.link_field}`"
            )

            if _join.columns:
                _columns.append(cls._columns_str(_join.columns, _as))

        return " ".join(_form), ",".join(_columns), _t


class Helper(object):

    @classmethod
    def create_table(cls, model_class):
        res = []
        table_name = model_class._meta['db_table']
        field_str = []
        for field_name in model_class._meta['fields']:
            field = model_class._meta['fields'][field_name]
            field_str.append(f"`{field_name}` {SQL.field(field)}")
            if field.attrs["unique"]:
                sql_str = f"ALTER TABLE `{table_name}` ADD CONSTRAINT `uni_{field_name}` UNIQUE (`{field_name}`)"
                res.append((sql_str, None))

            if field.attrs["index"]:
                sql_str = f"CREATE INDEX `idx_{field_name}` ON `{table_name}`(`{field_name}`)"
                res.append((sql_str, None))

        columns = ",".join(field_str)
        sql_str = f"CREATE TABLE `{table_name}`({columns})ENGINE=InnoDB"
        res.insert(0, (sql_str, None))
        return res

    @classmethod
    def drop_table(cls, model_class):
        sql_str = f"DROP TABLE IF EXISTS `{model_class._meta['db_table']}`"
        return [(sql_str, None)]

    @classmethod
    def alter_add(cls, model_class, field_name, field):
        """增加字段"""
        table_name = model_class._meta['db_table']
        sql_str = f"ALTER TABLE `{table_name}` ADD `{field_name}` {SQL.field(field)}"
        res = [(sql_str, None)]
        if field.attrs["unique"]:
            sql_str = f"ALTER TABLE `{table_name}` ADD CONSTRAINT `uni_{field_name}` UNIQUE (`{field_name}`)"
            res.append((sql_str, None))

        if field.attrs["index"]:
            sql_str = f"CREATE INDEX `idx_{field_name}` ON `{table_name}`(`{field_name}`)"
            res.append((sql_str, None))

        return res

    @classmethod
    def alter_drop(cls, model_class, field_name):
        """删除字段"""
        sql_str = f"ALTER TABLE `{model_class._meta['db_table']}` DROP `{field_name}`"
        return [(sql_str, None)]

    @classmethod
    def alter_change(cls, model_class, old_name, new_name, field):
        """重命名字段"""
        sql_str = f"ALTER TABLE `{model_class._meta['db_table']}` CHANGE `{old_name}` `{new_name}` {SQL.field(field)}"
        return [(sql_str, None)]

    @classmethod
    def alter_modify(cls, model_class, field_name, field):
        """变更数据类型"""
        sql_str = f"ALTER TABLE `{model_class._meta['db_table']}` MODIFY COLUMN `{field_name}` {SQL.field(field)}"
        return [(sql_str, None)]

    @classmethod
    def alter_constraint(cls, model_class, field_name, constraint):
        """变更约束"""
        table_name = model_class._meta['db_table']
        sql = None
        if constraint['k'] == 'unique':
            if constraint['v']:
                sql = f"ALTER TABLE `{table_name}` ADD CONSTRAINT `uni_{field_name}` UNIQUE (`{field_name}`)"
            else:
                sql = f"ALTER TABLE `{table_name}` DROP INDEX `uni_{field_name}`"
        return [(sql, None)]

    @classmethod
    def insert(cls, obj):
        keys = []
        values = []
        for k in obj._meta['fields']:
            keys.append(f"`{k}`")
            values.append(getattr(obj, k))

        sql = f"INSERT INTO `{obj._meta['db_table']}` ({','.join(keys)}) VALUES ({','.join(['%s']*len(keys))})"
        return [(sql, tuple(values))]

    @classmethod
    def update(cls, obj, fields):
        keys = []
        values = []
        for k in obj._meta['fields']:
            if fields == "__all__" or k in fields:
                keys.append(f'`{k}`')
                values.append(getattr(obj, k))

        primary_key = obj._meta['primary_key']
        sql = "UPDATE `{}` SET {} WHERE `{}`=%s".format(
            obj._meta['db_table'],
            ",".join(["{}=%s".format(k) for k in keys]),
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
        orders = kwargs.get('order_by', [])
        joins = kwargs.get('joins', ())
        lock = kwargs.get('lock', False)
        group_by = kwargs.get('group_by', ())

        _from, _columns, _as = Fmt._from_sql(model_class, columns, joins)
        sql = f"SELECT {_columns} FROM {_from}"
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

        sql += " FOR UPDATE" if lock else ""

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
    def unique_add(cls, model_class, columns):
        if not columns:
            return None, ""

        table_name = model_class._meta['db_table']

        if isinstance(columns, str):
            columns = [columns]

        index_name = cls.get_index_name("uni", columns)

        columns = ['`{}`'.format(x) for x in columns]

        sql = "ALTER TABLE `{}` ADD CONSTRAINT `{}` unique({})".format(table_name, index_name, ",".join(columns))

        return [(sql, None)], index_name

    @classmethod
    def unique_drop(cls, model_class, index_name):
        table_name = model_class._meta['db_table']

        sql = "ALTER TABLE `{}` DROP INDEX `{}`".format(table_name, index_name)

        return [(sql, None)]

