from pageserver.conf import settings
from datetime import datetime
import traceback


def log(*args):
    if settings.DEBUG:
        print(datetime.now(), *args)


def error(*args):
    if settings.DEBUG:
        print(traceback.print_exc())
        print('error 500', *args)
