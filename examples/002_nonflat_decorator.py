import logging
from logsense_opentracing.utils import setup_tracer, wait_on_tracer
from logsense_opentracing.instrumentation import patch_decorator, patch_single


# Define or import decorators (it should be done before patching)
def non_flat_decorator(first, second):
    def decorator(function):
        def decorated_function(*args, **kwargs):
            print('decorated')
            logging.info('First parameter is %s', first)
            result = function(*args, **kwargs)
            logging.info('Second parameter is %s', second)
            return result

        return decorated_function
    return decorator

# Decorator should be patched before using it.
patch_single('__main__.non_flat_decorator')
patch_decorator('__main__.non_flat_decorator')


# Use decorators
@non_flat_decorator(1, 17)
def hello_sphere_world():
    logging.info('Our world is sphere')


if __name__ == '__main__':
    # Initialize tracer
    setup_tracer(logsense_token='Your very own logsense token', dummy_sender=True)

    # Run application
    hello_sphere_world()

    # Tracer should be finished explicit, because of multithreading approach
    wait_on_tracer()
