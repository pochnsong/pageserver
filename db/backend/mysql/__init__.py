from pageserver.db.backend import BaseConnect
from pageserver.db.backend.utils import model_format, dict_format
from mysql.connector.pooling import MySQLConnectionPool
from .helper import Helper
import os
import string


class Connect(BaseConnect):

    def __init__(self, **kwargs):
        self.pool = MySQLConnectionPool(
            pool_name="mysql_pool", pool_size=16,
            **kwargs
        )

    def get_helper(self):
        return Helper

    def get_conn(self):
        return self.pool.get_connection()

    #def execute(self, sql_str, sql_params=None, conn=None):
    #    return self.commit(sql_str, sql_params, conn)

    def commands(self, commands, conn=None):
        cursor = None
        for sql, params in commands:
            cursor = self.commit(sql, params, conn)
        return cursor

    def commit(self, sql_str, sql_params=None, conn=None):
        _conn = conn or self.get_conn()
        cursor = _conn.cursor()
        try:
            cursor.execute(sql_str, sql_params)
            not conn and _conn.commit()
        finally:
            not conn and _conn.close()
        return cursor

    def insert(self, obj, conn=None):
        cursor = self.commands(Helper.insert(obj), conn=conn)

        primary_key = obj._meta['primary_key']
        if obj.instance is None:
            obj.instance = cursor.lastrowid
            setattr(obj, primary_key, obj.instance)

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

        commands = Helper.select(
            model_class, columns,
            where=where, skip=offset, limit=limit,
            lock=bool(conn), **kwargs)

        _conn = conn or self.get_conn()
        try:
            cursor = _conn.cursor(buffered=True, dictionary=False)
            for sql_str, values in commands:
                cursor.execute(sql_str, values)

            joins = kwargs.get('joins', ())
            res = cursor.fetchall()
            if to == 'dict':
                res = dict_format(res, columns, joins)
            elif to == 'model':
                res = model_format(res, columns, model_class, joins)
            return res
        except Exception as e:
            print(e, sql_str)
            raise e
        finally:
            not conn and _conn.close()

