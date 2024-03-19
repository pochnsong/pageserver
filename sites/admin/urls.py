from pageserver.views.static import serve
from pageserver.http.response import HttpRedirect
from .views.account import *
from .views.action import *
from .views.cache import *
from .views.overview import *
from .views.backup import *


urlpatterns = [
    ('', lambda x: HttpRedirect(f"{x.path}/index")),
    ('index', IndexView.as_view),
    ('ws/online', OnlineConsumer.as_view),
    ('static/(?P<path>.*)', serve, {'document_root': os.path.join(os.path.dirname(__file__),'static')}),

    ('api/login', LoginAPI.as_view),
    ('api/login/profile', LoginProfileAPI.as_view),

    ('api/model', ModelView.as_view),
    ('api/admin', AdminView.as_view),
    ('api/delete', DeleteObjsAPI.as_view),

    ('api/user/list', UserListAPI.as_view),
    ('api/user/edit', UserEditAPI.as_view),
    ('api/user/reset/password', UserResetPasswordAPI.as_view),

    ('api/cache/dbs', CacheDBAPI.as_view),
    ('api/cache/keys', CacheKeysAPI.as_view),
    ('api/cache/value', CacheValueAPI.as_view),
    ('api/cache/delete', CacheDeleteAPI.as_view),

    ('api/upload/block', UploadBlockFileAPI.as_view),
    ('api/backup/export', BackupExportView.as_view),
    ('ws/backup/import', BackupImportAPI.as_view),
]

__all__ = ["urlpatterns"]
