"""
Example of instrumentation of asynchronous functions
"""
import logging
import asyncio

from logsense_opentracing.utils import setup_tracer
from logsense_opentracing.instrumentation import patch_async_single

# Initialize tracer
setup_tracer(logsense_token='6bfd7d2f-7d45-414a-899d-f85175b08980')

loop = asyncio.get_event_loop()  # pylint: disable=invalid-name


async def finish():
    # Ensure all logs were sent correctly
    opentracing.tracer.finish()
    loop.stop()

async def func_1():  # pylint: disable=missing-docstring
    logging.info('Inside function 1')
    await asyncio.sleep(3)
    await func_2()
    logging.info('Going out function 1')

async def func_2():  # pylint: disable=missing-docstring
    logging.info('Inside function 2')

async def main():  # pylint: disable=missing-docstring
    logging.info('Main function start')
    await func_1()
    await func_2()
    logging.info('Main function end')
    asyncio.ensure_future(finish())


# Add instrumentation without doing enything in original functions
asyncio.ensure_future(patch_async_single('__main__.main'))
asyncio.ensure_future(patch_async_single('__main__.func_1'))
asyncio.ensure_future(patch_async_single('__main__.func_2'))

asyncio.ensure_future(main())
loop.run_forever()
