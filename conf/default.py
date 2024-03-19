import os
BASE_DIR = os.getcwd()
TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')
STATIC_DIR = os.path.join(BASE_DIR, 'static')
TEMP_DIR = os.path.join(BASE_DIR, 'tmp')

DEBUG = True

URLS = "urls"

# http 协议中间件
HTTP_MIDDLEWARE = []

# websocket 协议中间件
WS_MIDDLEWARE = []

# 自定义socket 中间件
SOCKET_MIDDLEWARE = []

SECRET_KEY = "CC,$G!&Nj?pRjiL}WkNq#?!D^ikj.kASOED1*~PNjn,s%8u->hvZ2bfJEe-+(&n1"

DATABASE = {
    "default": {
        "engine": "sqlite3",
        "name": os.path.join(BASE_DIR, "db.sqlite3")
    },
    #"admin": default,
    #"migrate": default,
}

#DATABASE = {
#    "default": {
#        "engine": "mysql",
#        "database": "database_name",
#        "user": "user_name",
#        "password": "password",
#        "unix_socket": "/path/to/mysqld.sock"
#    }
#}

CACHE = {
    "default": {
        "engine": "memory"
    }
}

LAYER = {
    "default": {
        "engine": "memory"
    }
}

ADMIN = {
    #"urls": "admin",
    #"config": "config",
}