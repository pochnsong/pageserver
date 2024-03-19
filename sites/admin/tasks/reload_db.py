"""
重新加载数据库
"""
import asyncio
import sys
import os
import json


def output(d):
    print(json.dumps(d))


def process(rf, models):
    from pageserver.db import Transaction
    info = json.loads(rf.readline())
    print(info)
    model_class = models[info['name']]
    columns = info['columns']
    count = 0

    with Transaction() as conn:
        model_class.query().use_conn(conn).delete()
        while line := rf.readline():
            if not line:
                return None

            if line[0] == '#':
                return line[1:].strip()

            dataset = json.loads(line)
            for v in dataset:
                d = dict(zip(columns, v))
                model_class(**d).save(conn=conn)
            count += len(dataset)
            output({'count': count, 'name': model_class.__name__})


async def main():
    base_dir = sys.argv[1]
    fname = sys.argv[2]
    os.chdir(base_dir)
    sys.path.insert(0, base_dir)
    from pageserver import PageApp

    app_settings = __import__('settings')
    app = PageApp(app_settings)
    await app.setup()

    from pageserver.conf import settings
    config = __import__(settings.ADMIN['config'])

    models = {}
    for model_class in config.MODEL_LIST:
        models[model_class.__name__] = model_class

    try:
        with open(fname) as rf:
            while line := rf.readline():
                if not line:
                    return None

                next_name = line.strip()[1:]
                while next_name:
                    next_name = process(rf, models)

            output({'status': 'finish'})

    except Exception as e:
        output({'errors': str(e)})

if __name__ == '__main__':
    asyncio.run(main())
