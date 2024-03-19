from pageserver.utils.asynctools import async_to_sync
from pageserver import PageApp
import settings as app_settings
import sys

from config import MODEL_LIST


def print_help():
    print("usage migrate [-t] 迁移模型")


async def exc_cmd():
    app = PageApp(app_settings)
    await app.setup()

    if len(sys.argv) == 1:
        print_help()
        exit()

    cmd = sys.argv[1]

    print(cmd)
    if cmd == 'migrate':
        from pageserver.manage import migrate
        migrate.run(MODEL_LIST)

    if cmd == 'setup':
        from pageserver.manage import setup
        setup.run(MODEL_LIST)

    if cmd == 'admin':
        from pageserver.sites.admin.model import Account
        from pageserver.manage import setup, migrate
        migrate.run([Account])


if __name__ == "__main__":
    async_to_sync(exc_cmd())


