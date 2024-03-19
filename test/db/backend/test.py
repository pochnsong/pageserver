
from pageserver.db.backend.mysql import Connect
from pageserver.db.query import Query
import asyncio

async def main():
    print("start")
    db = Connect(
        host="localhost", port=3306,
        user="root", password="Jyt_1234", db="nest")
    await db.setup()
    print("ok")
    obj = Account(username="cccc")
    obj.set_password("123456")
    await db.insert(obj)
    print(obj.id)

    await db.update(obj)

    query = Query(db, Account)
    print(await query.all())

loop = asyncio.get_event_loop()
loop.run_until_complete(main())