# imports
import logging
import opentracing
from logsense_opentracing.utils import setup_tracer, wait_on_tracer


def hello_logsense():
    """
    Do nothing, just log
    """
    logging.info('Hello logsense')


if __name__ == '__main__':
    # Initialize tracer
    setup_tracer(logsense_token='Your very own logsense token')

    # Run application
    with opentracing.tracer.start_active_span('hello'):
        hello_logsense()

    # Tracer should be finished explicitly, because of multithreading approach
    wait_on_tracer()
