import asyncio
import inspect
import functools


def async_to_sync(task):
    asyncio.run(task)


async def sync_to_async(func, / , *args, **kwargs):
    return func(*args, **kwargs)


async def file(path, mode='rb'):
    def func(p, m):
        with open(p, m) as rf:
            return rf.read()
    return await asyncio.to_thread(func, path, mode)


async def cancel_tasks(tasks):
    for task in tasks:
        task.cancel()
        try:
            await task
        except:
            pass

async def await_many_dispatch(funcs, dispatch, tasks=None):
    """
    Given a set of consumer callables, awaits on them all and passes results
    from them to the dispatch awaitable as they come in.
    """
    # Start them all off as tasks

    if tasks is None:
        tasks = []
    for func in funcs:
        tasks.append(asyncio.create_task(func()))

    try:
        while True:
            # Wait for any of them to complete
            await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            # Find the completed one(s), yield results, and replace them
            for i, task in enumerate(tasks):
                if task.done():
                    result = task.result()
                    await dispatch(result)
                    tasks[i] = asyncio.create_task(funcs[i]())
    finally:
        # Make sure we clean up tasks on exit
        await cancel_tasks(tasks)

class TaskGroup:
    def __init__(self):
        self._loop = None
        self._tasks = set()
        self._wait_result = None
    async def __aenter__(self):
        if not self._loop:
            self._loop = asyncio.get_running_loop()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        try:
            while self._tasks:
                self._wait_result = self._loop.create_future()
                await self._wait_result
        except asyncio.CancelledError:
            pass

    def _on_task_done(self, task):
        self._tasks.discard(task)

        if self._wait_result is not None and not self._tasks:
            self._wait_result.set_result(True)
        try:
            if task.exception():
                for task in self._tasks:
                    task.cancel()
        except:
            pass


    def create_task(self, coro):
        task = self._loop.create_task(coro)
        task.add_done_callback(self._on_task_done)
        self._tasks.add(task)
        return task

async def test():

    async def f0():
        while True:
            await asyncio.sleep(1)
            print("f0")

    async def f1():
        await asyncio.sleep(1)
        print("f1")
        return 1
    async def f2():
        await asyncio.sleep(1.5)
        print("f2")
        return 2

    async def f3():
        await asyncio.sleep(3)
        raise Exception()


    async def c(v):
        print(v)
    #await await_many_dispatch([f1, f2], c)
    async with TaskGroup() as group:
        group.create_task(f0())
        group.create_task(f0())
        group.create_task(f1())
        group.create_task(f2())
        group.create_task(f3())

    print("end")

if __name__ == "__main__":
    asyncio.run(test())