from pageserver.views.generic import *
from pageserver.conf import settings
from .account import check_perm
config = __import__(settings.ADMIN['config'])


class ModelView(API):
    def check_perm(self):
        return check_perm(self.request)

    def get(self, request):
        models = []
        for model in config.MODEL_LIST:
            models.append({
                'label': model._meta['label'],
                'model_name': model.__name__,
            })
        return {'status': 'OK', 'model_list': models}


class AdminView(AdminAPI):
    def check_perm(self):
        return check_perm(self.request)

    def get_model_class(self):
        try:
            for model_class in config.MODEL_LIST:
                if model_class.__name__ == self.request.GET['model']:
                    return model_class

        except:
            return None


class DeleteObjsAPI(API):

    def check_perm(self):
        return check_perm(self.request)


    def get_model_class(self):
        try:
            for model_class in config.MODEL_LIST:
                if model_class.__name__ == self.request.GET['model']:
                    return model_class
        except:
            return None

    def post(self, request):
        try:
            model_class = self.get_model_class()
            key = model_class._meta['primary_key']
            pks = [int(x) for x in request.POST.getlist('pks')]
            model_class.query(**{f"{key}__in": pks}).delete()
            return {'status': 'OK'}
        except Exception as e:
            return {'status': 'FAIL', 'errors': '无法删除'}

