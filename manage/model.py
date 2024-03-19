from pageserver.db.models import Model
from pageserver.db.fields import *


class Migration(Model):
    id = AutoField(primary_key=True)
    model_name = CharField(max_length=64)
    field_info = TextField()
    constraint = TextField()
    update_time = BigIntegerField(default=-1)

    meta = {
        'db_table': 'migration',
        'use_db': 'migrate',
    }