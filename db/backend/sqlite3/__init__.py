from pageserver.db.backend import BaseConnect
from pageserver.db.backend.utils import *
import sqlite3
from .helper import Helper


class Connect(BaseConnect):

    def __init__(self, db_name):
        self.db_name = db_name

    def get_helper(self):
        return Helper

    def get_conn(self):
        return sqlite3.connect(self.db_name)

    def commit(self, sql_str, sql_params=None, conn=None):
        if sql_params is None:
            sql_params = ()
        error = None
        _conn = conn
        if conn is None:
            _conn = self.get_conn()
        cursor = _conn.cursor()
        try:
            cursor.execute(sql_str, sql_params)
        except Exception as e:
            #print(sql_str, sql_params)
            error = e

        if conn is None:
            _conn.commit()
            _conn.close()

        if error:
            raise error
        return cursor

    def commands(self, commands, conn=None):
        cursor = None
        for args in commands:
            cursor = self.commit(args[0], args[1], conn=conn)
        return cursor

    def insert(self, obj, conn=None):
        _conn = conn
        if not conn:
            _conn = self.get_conn()

        cursor = self.commands(Helper.insert(obj), conn)

        primary_key = obj._meta['primary_key']
        obj_id = getattr(obj, primary_key)
        if obj_id is None:
            obj.instance = cursor.lastrowid
            setattr(obj, primary_key, obj.instance)

        if not conn:
            _conn.close()

    def update(self, obj, conn=None, fields="__all__"):
        self.commands(Helper.update(obj, fields), conn)

    def delete(self, model_class, where, conn=None):
        """
        where
        order_by = [(column, asc),]
        """
        self.commands(Helper.delete(model_class, where), conn)

    def select(self, model_class, columns,
               where=None, offset=None, limit=None,
               to="model", conn=None, **kwargs):
        """
        where
        order_by = [(column, asc),]
        """
        joins = kwargs.get('joins', ())

        if not conn:
            _conn = self.get_conn()
            lock = False
        else:
            _conn = conn
            lock = True

        commands = Helper.select(
            model_class, columns,
            where, offset, limit, **kwargs)

        cursor = self.commands(commands, _conn)

        res = cursor.fetchall()
        if to == 'list':
            pass
        elif to == 'dict':
            res = dict_format(res, columns, joins)
        else:
            res = model_format(res, columns, model_class, joins)

        if conn is None:
            _conn.close()

        return res
