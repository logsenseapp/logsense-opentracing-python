"""
Example of instrumentation of asynchronous functions
"""
import asyncio
from logsense_opentracing.instrumentation import patch_async_single


loop = asyncio.get_event_loop()  # pylint: disable=invalid-name


async def funct_1():  # pylint: disable=missing-docstring
    print('Inside function 1')
    await asyncio.sleep(3)
    await funct_2()
    print('Going out function 1')

async def funct_2():  # pylint: disable=missing-docstring
    print('Inside function 2')

async def main():  # pylint: disable=missing-docstring
    print('Main function start')
    await funct_1()
    await funct_2()
    print('Main function end')


asyncio.ensure_future(patch_async_single('__main__.main'))
asyncio.ensure_future(patch_async_single('__main__.funct_1'))
asyncio.ensure_future(patch_async_single('__main__.funct_2'))

asyncio.ensure_future(main())
loop.run_forever()
