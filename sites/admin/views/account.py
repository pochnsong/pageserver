from pageserver.views.generic import *
from pageserver.utils.crypto import get_random_string
from pageserver.http.exception import Error
from pageserver.utils.byteslib import bytes2hex
from pageserver.utils.crypto import create_cipher_token
from pageserver.cache import cache
from ..model import AdminAccount
from ..secrets import Secrets, decrypt, SM4
from ..settings import SECRET_KEY_SM4
import json
import re

def check_perm(request):
    return bool(getattr(request, 'admin', False))

class LoginAPI(API):
    def get_once(self, user_pk, sm4):
        once = 'login' + get_random_string(length=16)
        cache.set(once, {'pk': user_pk, 'sm4': sm4}, timeout=300)
        return once

    def get(self, request):
        if check_perm(request):
            return {'status': 'OK', 'once': self.get_once(request.admin.id, request.sm4)}
        return {'status': 'FAIL'}

    def post(self, request):
        try:
            key = Secrets.key_exchange(request.POST['pubkey'])
            data = json.loads(decrypt(request.POST['data'], key))
            username = data['usr']
            password = data['pwd']

            if not re.match(r"^[\w\d]{4,32}$", username):
                raise Exception()

            obj = AdminAccount.query(username=username).one()

            if not obj:
                raise Exception()

            if obj.check_password(password):
                sm4_key = bytes2hex(key)
                val = {
                    'id': obj.id,
                    '_': obj.update_time,
                    'sm4': sm4_key
                }
                sm4 = SM4(SECRET_KEY_SM4)
                token = create_cipher_token(val, sm4, expire=60*60*12)
                request.sm4 = sm4_key
                return {
                    'status': 'OK',
                    'loginid': {
                        'key': 'aid',
                        'token': token,
                    },
                    'once': self.get_once(obj.id, sm4_key)
                }
        except Exception as e:
            import traceback
            traceback.print_exc()
            pass

        return {'status': 'FAIL', 'errors': '用户名和密码错误'}


class LoginProfileAPI(API):
    def check_perm(self):
        return check_perm(self.request)

    def get(self, request):
        return {
            'status': 'OK',
            'profile': self.request.admin.to_dict(fields=["username", "nickname", "create_time", "token"])
        }


class UserListAPI(ListAPI):
    model_class = AdminAccount
    fields = "__all__"
    exclude = ["password", "keygen"]
    filters = ('id', )

    def check_perm(self):
        return check_perm(self.request)


class UserEditAPI(API):
    fields = ['nickname', 'is_super', 'is_active']

    def check_perm(self):
        if check_perm(self.request):
            return self.request.admin.is_super
        return False

    def post(self, request):
        try:
            if 'id' in request.POST:
                obj = AdminAccount.query(id=int(request.POST['id'])).one()
                for k in self.fields:
                    if k in request.POST:
                        setattr(obj, k, request.POST[k])

                obj.save(fields=self.fields)
            else:
                obj = AdminAccount(
                    username=request.POST['username'],
                    nickname=request.POST['nickname'],
                    is_super=request.POST['is_super'],
                    is_active=request.POST['is_active'],
                )
                password = request.POST['password'][:128]
                if len(password)<8:
                    raise Error("密码长度小于8")
                obj.set_password(raw_password=password)
                obj.save()

            return {'status': 'OK'}
        except Error as e:
            return {'status': 'FAIL', 'errors': str(e)}
        except Exception as e:
            if 'unique' in str(e).lower():
                return {'status': 'FAIL', 'errors': "用户名重复"}
            return {'status': 'FAIL', 'errors': "错误的请求"}

    def delete(self, request):
        try:
            pk = int(request.GET.get('pk'))
            if self.request.admin.id == pk:
                return {'status': 'FAIL', 'errors': '不能删除自己'}
            obj = AdminAccount.query(id=pk).one()
            obj.delete()
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {'status': 'FAIL', 'errors': '无法删除'}
        return {'status': 'OK'}


class UserResetPasswordAPI(API):
    def check_perm(self):
        return check_perm(self.request)

    def post(self, request):
        try:
            obj = AdminAccount.query(id=int(request.POST['id'])).one()
            if request.admin.is_super or obj.id == request.admin.id:
                password = request.POST['password']
                if len(password) < 8:
                    raise Error("密码长度小于8")
                obj.set_password(raw_password=password)
                obj.save(fields=['password', 'token'])
                return {'status': 'OK', 'self': obj.id == request.admin.id}

            else:
                raise Error("错误的参数")
        except Error as e:
            return {'status': 'FAIL', 'errors': str(e)}
        except:
            return {'status': 'FAIL', 'errors': '错误的参数'}
