
class BaseConnect(object):

    def get_conn(self):
        raise NotImplementedError

    def insert(self, obj, conn=None):
        raise NotImplementedError

    def update(self, obj, conn=None, fields="__all__"):
        raise NotImplementedError

    def delete(self, model_class, where, conn=None):
        raise NotImplementedError

    def select(self, model_class, columns, where=None, offset=None, limit=None, **kwargs):
        raise NotImplementedError

    def create_table(self, model_class):
        """根据model_class创建表"""
        raise NotImplementedError

