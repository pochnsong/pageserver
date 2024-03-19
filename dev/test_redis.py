"""
测试redis同步和异步协程之间的性能差异
"""
import codecs

import asyncio
import redis
import redis.asyncio as aioredis
import time
N = 10000

def get_sync(conn, name):
    return conn.get(name)

def test_sync():
    conn = redis.StrictRedis("localhost", port=6379, db=0)
    conn.set("test", "123456")
    t = time.time()
    for i in range(N):
        conn.set("test", i)
        get_sync(conn, "test")

    print("sync time", time.time()-t)
    conn.close()

async def get_async(conn, name, v=0):
    await conn.set(name, v)
    return await conn.get(name)

async def test_async():
    conn = aioredis.Redis()

    await conn.set("test", "123456")
    t = time.time()
    async with asyncio.TaskGroup() as group:
        for i in range(N):
            group.create_task(get_async(conn, name="test", v=i))

    print(f"async time (single)", time.time()-t)
    await conn.aclose()

async def get_async_pool(pool, name, v=0):
    conn = aioredis.Redis(connection_pool=pool)
    await conn.set(name, v)
    res = await conn.get(name)
    await conn.aclose()
    return res

async def test_async_pool():
    pool = aioredis.ConnectionPool.from_url("redis://localhost")
    t = time.time()
    async with asyncio.TaskGroup() as group:
        for i in range(N):
            group.create_task(get_async_pool(pool, name="test", v=i))
    print(f"async time (pool)", time.time()-t)
    await pool.aclose()

if __name__ == "__main__":
    test_sync()
    conn = redis.StrictRedis("localhost", port=6379, db=0)
    print(conn.get("test"))
    conn.close()
    asyncio.run(test_async())

    conn = redis.StrictRedis("localhost", port=6379, db=0)
    print(conn.get("test"))
    conn.close()

    asyncio.run(test_async_pool())
    conn = redis.StrictRedis("localhost", port=6379, db=0)
    print(conn.get("test"))
    conn.close()
