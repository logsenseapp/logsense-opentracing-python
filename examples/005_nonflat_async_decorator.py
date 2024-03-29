import logging
import functools
from asyncio import get_event_loop
from logsense_opentracing.utils import setup_tracer, wait_on_tracer
from logsense_opentracing.instrumentation import patch_async_decorator


# Define or import decorators (it should be done before patching)
def non_flat_decorator(first, second):
    def decorator(function):
        @functools.wraps(function)
        async def decorated_function(*args, **kwargs):
            logging.info('First parameter is %s', first)
            result = await function(*args, **kwargs)
            logging.info('Second parameter is %s', second)
            return result

        return decorated_function
    return decorator

# Decorator should be patched before using it.
patch_async_decorator('__main__.non_flat_decorator', flat=False)


# Use decorators
@non_flat_decorator(1, 17)
async def hello_sphere_world():
    logging.info('Our world is sphere')


if __name__ == '__main__':
    # Initialize tracer
    setup_tracer(component='non flat async decorator')

    # Run application
    get_event_loop().run_until_complete(hello_sphere_world())

    # Tracer should be finished explicit, because of multithreading approach
    wait_on_tracer()
