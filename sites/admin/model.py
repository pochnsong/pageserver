from pageserver.db.models import *
from pageserver.utils.crypto import check_password, make_password
from pageserver.utils.time import get_timestamp, bj_now


class AdminAccount(Model):
    id = BigAutoField(primary_key=True)
    username = VarCharField(max_length=32, unique=True, re=r"[a-zA-Z0-9]{4,32}")
    keygen = VarCharField(max_length=256, default=None)
    password = VarCharField(max_length=128, nullable=False, safe=True)
    nickname = VarCharField(max_length=16, default="", re=r"[a-zA-Z0-9\u4e00-\u9fa5]{0,16}")
    is_super = BoolField(default=False)
    is_active = BoolField(default=True)
    create_time = BigTimestampField(default=get_timestamp)
    update_time = BigIntegerField(default=get_timestamp)

    meta = {
        'db_table': 'admin_account',
        'label': '运维帐号',
        'use_db': 'admin',
    }

    def __str__(self):
        return f"{self.username}.{self.password}"

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    def set_password(self, raw_password, keygen=None):
        # 每次保存密码重置token
        self.password = make_password(raw_password)
        self.keygen = keygen
        self.update_time = get_timestamp()

    def pre_save(self):
        if not self.create_time:
            self.create_time = get_timestamp()

        if not self.password.startswith('pbkdf2_sha256$'):
            self.set_password(self.password)

        super().pre_save()


    def check_keygen(self, raw_key):
        now = bj_now()
        return True


