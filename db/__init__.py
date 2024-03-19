"""
DATABASE = {
    'default': {
        'engine': 'django.db.backends.sqlite3',
        'name': 'nest',
    }
}
"""


class Transaction(object):
    def __init__(self, conn=None, alias="default"):
        self.auto_close = False
        self.conn = conn

        if not conn:
            self.auto_close = True
            self.conn = database[alias].get_conn()

    def __enter__(self):
        return self.conn

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type:
            self.conn.rollback()
        else:
            self.conn.commit()

        if self.auto_close:
            self.conn.close()


class Database:
    dbs = {}

    @classmethod
    def create_engine(cls, engine, **kwargs):
        if engine == "sqlite3":
            from .backend import sqlite3
            return sqlite3.Connect(db_name=kwargs["name"])
        elif engine == "mysql":
            from .backend import mysql
            return mysql.Connect(**kwargs)
        else:
            print("unknown database engine {}".format(kwargs['engine']))

    def setup(self, config):
        for k, v in config.items():
            self.dbs[k] = self.create_engine(**v)

        if 'migrate' not in self.dbs:
            self.dbs['migrate'] = self.dbs['default']

        if 'admin' not in self.dbs:
            self.dbs['admin'] = self.dbs['default']

    def __getitem__(self, item):
        return self.dbs[item]



database = Database()


__all__ = ["database", "Transaction"]

