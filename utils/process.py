"""
后台运行
"""

from multiprocessing import Process
import asyncio


def run(f, args):
    p = Process(target=f, args=args)
    p.start()


async def shell(cmd):
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)

    stdout, stderr = await proc.communicate()
    return stdout, stderr
