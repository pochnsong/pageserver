"""
重新加载数据库
"""
import asyncio
import sys
import os
import json


def output(d):
    print(json.dumps(d))


def process(rf, model_cnf):
    from pageserver.db import Transaction

    line = rf.readline()
    model_class = model_cnf['model']
    model_name = model_cnf['name']
    columns = model_cnf['columns']
    count = 0
    with Transaction() as conn:
        model_class.query().use_conn(conn).delete()
        while line:
            if not line:
                return None
            if line[0] == '#':
                return line[1:].strip()

            dataset = json.loads(line)
            for v in dataset:
                d = dict(zip(columns, v))
                model_class(**d).save(conn=conn)
            count += len(dataset)
            output({'count': count, 'name': model_name})
            line = rf.readline()


async def main():
    base_dir = sys.argv[1]
    fk = sys.argv[2]
    os.chdir(base_dir)
    sys.path.insert(0, base_dir)
    from pageserver import PageApp

    app_settings = __import__('settings')
    app = PageApp(app_settings)
    await app.setup()

    from pageserver.conf import settings
    config = __import__(settings.ADMIN['config'])

    cnf = {}

    try:
        with open(os.path.join(settings.TEMP_DIR, fk)) as rf:
            for o in json.loads(rf.readline()):
                cnf[o['name']] = o

            for model_class in config.MODEL_LIST:
                if model_class.__name__ in cnf:
                    cnf[model_class.__name__]['model'] = model_class

            next_name = rf.readline()[1:].strip()
            while next_name:
                next_name = process(rf, cnf[next_name])

            output({'status': 'finish'})

    except Exception as e:
        output({'errors': str(e)})

if __name__ == '__main__':
    asyncio.run(main())
