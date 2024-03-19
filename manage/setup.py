from pageserver.db import database
from pageserver.db import database, fields, Transaction
from pageserver.utils.time import get_timestamp
from pageserver.conf import settings
import json
from .migrate import to_dict
from .model import Migration


def _run(model_list, conn, conn_migrate):
    for model_class in model_list:
        db = database[model_class._meta['use_db']]
        helper = db.get_helper()
        print(f'初始化 {model_class.__name__}:{model_class._meta["db_table"]} @{db}')
        commands = helper.drop_table(model_class)
        commands += helper.create_table(model_class)
        constraint = {'unique_together': None}

        db_name = model_class._meta['use_db']
        db_table = f"{db_name}.{model_class._meta['db_table']}"
        if "unique_together" in model_class._meta:
            _commands, unique_name = helper.unique_add(model_class, model_class._meta["unique_together"])
            commands += _commands
            constraint['unique_together'] = unique_name

        db.commands(commands, conn)

        obj = Migration(
            model_name=db_table,
            field_info=json.dumps(to_dict(model_class), ensure_ascii=False),
            constraint=json.dumps(constraint, ensure_ascii=False),
            update_time=get_timestamp()
        )
        obj.save(conn=conn_migrate)


def run(model_list):
    alias = {}
    if settings.ADMIN:
        from pageserver.sites.admin.model import AdminAccount
        alias['admin'] = [AdminAccount]

    # 数据库引擎归类
    for model_class in model_list:
        db_name = model_class._meta['use_db']
        if db_name not in alias:
            alias[db_name] = []
        alias[db_name].append(model_class)

    print(alias)

    migrate_db = Migration._meta['use_db']
    db = database['migrate']
    helper = db.get_helper()

    with Transaction(alias=migrate_db) as conn_migrate:
        db.commands(helper.drop_table(Migration), conn_migrate)
        db.commands(helper.create_table(Migration), conn_migrate)

        for db_name in alias:
            if database[migrate_db] == database[db_name]:
                _run(alias[db_name], conn_migrate, conn_migrate)
            else:
                with Transaction(alias=db_name) as conn:
                    _run(alias[db_name], conn, conn_migrate)

