import logging
import functools
from asyncio import get_event_loop
from logsense_opentracing.utils import setup_tracer, wait_on_tracer
from logsense_opentracing.instrumentation import patch_async_decorator


# Define or import decorators (it should be done before patching)
def flat_decorator(function):
    @functools.wraps(function)
    async def decorated_function(*args, **kwargs):
        logging.info('Before executing function as flat')
        result = await function(*args, **kwargs)
        logging.info('After executing function as flat')
        return result

    return decorated_function

# Decorator should be patched before using it.
patch_async_decorator('__main__.flat_decorator', flat=True)


# Use decorators
@flat_decorator
async def hello_flat_world():
    logging.info('Our world is flat')


if __name__ == '__main__':
    # Initialize tracer
    setup_tracer(logsense_token='Your very own logsense token', dummy_sender=True)

    # Run application
    get_event_loop().run_until_complete(hello_flat_world())

    # Tracer should be finished explicit, because of multithreading approach
    wait_on_tracer()
