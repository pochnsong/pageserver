from pageserver.db import database, fields, Transaction
from pageserver.utils.time import get_timestamp
from .model import Migration
import json
from copy import deepcopy
from . import *

def wait_select(question, choices):
    while True:
        res = input(question)
        if len(choices) == 1 and not res:
            print(choices)
            return choices[0]
        if res in choices:
            return res

def to_dict(model_class):
    fields = {}
    for k, field in model_class._meta['fields'].items():
        attrs = {}
        for _k, _v in field.attrs.items():
            if callable(_v):
                continue
            attrs[_k] = _v
        fields[k] = attrs
        fields[k]['__type__'] = field.__class__.__name__

    return fields


def _compare(d1, d2):
    # old, new
    constraint = ["unique", "nullable", "index"]

    attrs = []
    for k, v in d2.items():
        if k not in constraint:
            continue
        if k not in d1:
            attrs.append({
                'k': k,
                'v': v,
                '_': 'new'
            })

    for k, v1 in d1.items():
        if k not in constraint:
            continue
        if k not in d2:
            attrs.append({
                'k': k,
                'v': v1,
                '_': 'rm',
            })
            continue

        v2 = d2.get(k)
        if v1 == v2:
            continue

        attrs.append({
            'k': k,
            'v': v2,
            '_': 'ch'
        })

    return attrs


def compare(m1, m2):
    # old ,new
    f_rm = deepcopy(m1)
    f_new = {}
    f_mv = []
    f_attr = {}
    f_type = {}
    m2 = deepcopy(m2)

    for k, v2 in m2.items():
        if k not in m1:
            f_new[k] = v2
            continue

        v1 = f_rm.get(k)
        del f_rm[k]
        _attrs = _compare(v1, v2)
        if _attrs:
            f_attr[k] = _attrs

        if v2["__type__"] != v1["__type__"]:
            f_type[k] = v2

    if f_new and f_rm:
        for k in list(f_rm.keys()):
            res = wait_select("是否重命名 {}?[y/n]".format(k), ['y', 'n'])
            if res == 'y':
                names = list(f_new.keys())
                res = wait_select("输入重命名字段: 可选[{}]".format(",".join(names)), names)
                f_mv.append([k, res, f_new[res]])
                del f_new[res]
                del f_rm[k]

    return f_new, f_rm, f_mv, f_attr, f_type


def _run(model_list, conn, conn_migrate, commit=True):
    for model_class in model_list:
        print(model_class)
        db_name = model_class._meta['use_db']
        db = database[db_name]
        helper = db.get_helper()
        db_table = get_model_name(model_class)

        model_info = to_dict(model_class)
        obj = Migration.query(model_name=db_table).use_conn(conn_migrate).one()
        if obj is None:
            print('新建数据表', db_table)
            db.commands(helper.create_table(model_class), conn=conn)

            obj = Migration(
                model_name=db_table,
                field_info=json.dumps(model_info, ensure_ascii=False),
                update_time=get_timestamp()
            )
            if commit:
                obj.save(conn=conn_migrate)
            continue
        else:
            # 比较

            m1 = json.loads(obj.field_info)
            add_fields, drop_fields, rename_fields, field_constraints, modify_fields = compare(m1, model_info)

            commands = []
            if add_fields:
                print(f'[{db_table}] 增加字段', add_fields)
                for k, attrs in add_fields.items():
                    field_class = getattr(fields, attrs['__type__'])
                    del attrs['__type__']
                    field = field_class(**attrs)
                    commands += helper.alter_add(model_class, k, field)

            if drop_fields:
                print(f'[{db_table}] 删除字段', drop_fields)
                for k in drop_fields:
                    commands += helper.alter_drop(model_class, k)

            if rename_fields:
                print(f'[{db_table}] 重命名字段', rename_fields)
                for k1, k2, attrs in rename_fields:
                    field_class = getattr(fields, attrs['__type__'])
                    del attrs['__type__']
                    field = field_class(**attrs)
                    commands += helper.alter_change(model_class, k1, k2, field)

            if modify_fields:
                print(f'[{db_table}] 变更字段', modify_fields)

            for k, attrs in modify_fields.items():
                field_class = getattr(fields, attrs['__type__'])
                field = field_class(**attrs)
                commands += helper.alter_modify(model_class, k, field)

            if field_constraints:
                print(f'[{db_table}] 变更约束', field_constraints)

                for field_name in field_constraints:
                    for constraint in field_constraints[field_name]:
                        commands += helper.alter_constraint(model_class, field_name, constraint)

            # unique_together
            new_unique_name = ""
            old_unique_name = ""
            unique_commands = []
            if obj.constraint:
                old_constraint = json.loads(obj.constraint)
                old_unique_name = old_constraint['unique_together']

            if "unique_together" in model_class._meta:
                unique_commands, new_unique_name = helper.unique_add(model_class, model_class._meta["unique_together"])

            if old_unique_name != new_unique_name:
                if old_unique_name:
                    print('删除旧约束', old_unique_name)
                    commands += helper.unique_drop(model_class, old_unique_name)

                if new_unique_name:
                    print('添加新约束', new_unique_name)
                    commands += unique_commands

            if commit:
                db.commands(commands, conn=conn)
                obj.field_info = json.dumps(model_info, ensure_ascii=False)
                obj.constraint = json.dumps({
                    "unique_together": new_unique_name
                })
                obj.update_time = get_timestamp()
                obj.save(conn=conn_migrate)


def run(model_list, commit=True):
    alias = {}
    # 数据库引擎归类
    for model_class in model_list:
        db_name = model_class._meta['use_db']
        if db_name not in alias:
            alias[db_name] = []
        alias[db_name].append(model_class)

    migrate_db = Migration._meta['use_db']
    with Transaction(alias=migrate_db) as conn_migrate:
        for db_name in alias:
            if database[migrate_db] == database[db_name]:
                _run(alias[db_name], conn_migrate , conn_migrate, commit=commit)
            else:
                with Transaction(alias=db_name) as conn:
                    _run(alias[db_name], conn, conn_migrate, commit=commit)


def clean(model_list):
    alias = {}
    # 数据库引擎归类
    models = []
    for model_class in model_list:
        models.append(get_model_name(model_class))

    for table in Migration.query().all():
        print(table.model_name)
        if table.model_name not in models:
            print(f'delete {table.model_name}')
            table.delete()
