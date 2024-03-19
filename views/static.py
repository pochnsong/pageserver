from pageserver.http.response import HttpResponse, Http405, Http404, FileResponse
import mimetypes
import os
import urllib.parse
from pageserver.cache import GLOBAL


def serve(request, path, document_root=None, show_indexes=False):
    """
    静态请求
    """
    GLOBAL.STATIC_REQUEST += 1
    path = urllib.parse.unquote(path)
    fullpath = os.path.join(document_root, path)
    if not os.path.exists(fullpath):
        return Http404()

    if os.path.isdir(fullpath):
        if show_indexes:
            return HttpResponse('list')
        return Http405("Directory indexes are not allowed here.")

    content_type, encoding = mimetypes.guess_type(str(fullpath))
    if path.lower().endswith('.js'):
        content_type = 'text/javascript'
    else:
        content_type = content_type or 'application/octet-stream'

    return FileResponse(open(fullpath, 'rb'), filename=os.path.basename(path), content_type=content_type)
