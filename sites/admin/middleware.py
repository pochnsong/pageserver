from pageserver.http.exception import Error
from pageserver.utils.crypto import check_cipher_token
from pageserver.http.query_dict import QueryDict
from pageserver.utils.gmsm.sm4 import SM4
from pageserver.utils.generic import *
from .model import AdminAccount
from .secrets import encrypt, decrypt
from .settings import SECRET_KEY_SM4
import json

token_sm4 = SM4(SECRET_KEY_SM4)
"""
加密流程
带sm4的request, get, body 会被加密
"""

class TokenMiddleware(object):
    def get_account_obj(self, model_class, pk, t):
        obj = get_obj(model_class, pk, fields_exclude=["password"])
        if t != obj.update_time:
            raise Error('re-login')
        if not obj.is_active:
            raise Error("帐号已锁定")
        return obj

    def request_handle(self, request):
        if token := check_cipher_token(request.META.get('aid'), token_sm4):
            request.admin = self.get_account_obj(AdminAccount, token['id'], token['_'])
            if 'sm4' in token:
                request.sm4 = token['sm4']
                if request.body:
                    request.POST = QueryDict(json.loads(decrypt(request.body.decode('utf-8'), request.sm4)))
                if 'q' in request.GET:
                    request.GET = QueryDict(json.loads(decrypt(request.GET['q'], request.sm4)))

    def response_handle(self, request, response):
        if sm4_key := getattr(request, 'sm4', None):
            response.body = encrypt(response.body, sm4_key).encode('utf-8')
            response.content_type = "text/sm4"
