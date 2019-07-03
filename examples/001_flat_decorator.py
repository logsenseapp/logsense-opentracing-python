import logging
from logsense_opentracing.utils import setup_tracer, wait_on_tracer
from logsense_opentracing.instrumentation import patch_decorator, patch_single


# Define or import decorators (it should be done before patching)
def flat_decorator(function):
    def decorated_function(*args, **kwargs):
        logging.info('Before executing function as flat')
        result = function(*args, **kwargs)
        logging.info('After executing function as flat')
        return result

    return decorated_function

# Decorator should be patched before using it.
patch_decorator('__main__.flat_decorator', flat=True)


# Use decorators
@flat_decorator
def hello_flat_world():
    logging.info('Our world is flat')


if __name__ == '__main__':
    # Initialize tracer
    setup_tracer(logsense_token='Your very own logsense token')

    # Run application
    hello_flat_world()

    # Tracer should be finished explicit, because of multithreading approach
    wait_on_tracer()
