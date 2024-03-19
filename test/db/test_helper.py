from pageserver.db.models import *
from pageserver.db.query import Q
from pageserver.db.function import *
from pageserver.db.backend.sqlite3 import Helper as HelperSqlite
from pageserver.db.backend.mysql import Helper as HelperMysql


class ModelA(Model):
    id = AutoField()
    name = CharField(max_length=8)

class ModelB(Model):
    id = AutoField()
    aid = IntegerField()


def main():
    join={
        "field": "aid",
        "model_class": ModelA,
        "link_name": "model_a",
    }
    queryset = Query(db="test", model_class=ModelB).query().join(**join)

    """

    sql_str, values = HelperSqlite.select(
        ModelA, queryset._columns,
        queryset._where.where, None, None, order_by="",
        joins=None, lock=True)

    print(sql_str)
    print(values)

    sql_str, values = HelperSqlite.select(
        ModelA, queryset._columns,
        queryset._where.where, 1, 100, order_by="",
        joins=queryset._join, lock=True)

    print(sql_str)
    print(values)

    sql_str, values = HelperMysql.select(
        ModelA, queryset._columns,
        queryset._where.where, offset=None, limit=None, order_by="",
        joins=None, lock=True)

    print(sql_str)
    print(values)

    sql_str, values = HelperMysql.select(
        ModelA, queryset._columns,
        queryset._where.where, offset=1, limit=100, order_by="",
        joins=queryset._join, lock=True)

    print(sql_str)
    print(values)


    queryset = Query(db="test", model_class=ModelB).query(['id', Sum('aid')]).join(**join)

    sql_str, values = HelperSqlite.select(
        ModelA, ["id", Sum('id')],
        queryset._where.where, None, None, order_by="",
        joins=None, lock=True)

    print(sql_str)
    print(values)

    sql_str, values = HelperSqlite.select(
        ModelA, [Count('*')],
        queryset._where.where, None, None, order_by="",
        lock=True)

    print(sql_str)
    print(values)
    """

    sql_str, values = HelperMysql.select(
        ModelA, ["id", Count('tag_id')],
        queryset._where.where, offset=None, limit=None, order_by="",
        group_by=["tag_id"],
        joins=None, lock=True)

    print(sql_str)
    print(values)


    sql_str, values = HelperMysql.delete(
        ModelA, Q())

    print(sql_str)
    print(values)

    pass


if __name__ == "__main__":
    main()
