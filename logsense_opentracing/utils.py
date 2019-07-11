"""
Logsense opentracer comes with some handle functions for minimize amount of work
and understanding of opentracing complexity

Here is shortest example of using opentracing with logsense tracer::

    # imports
    import logging
    import opentracing
    from logsense_opentracing.utils import setup_tracer, wait_on_tracer


    def hello_logsense():
        \"""
        Do nothing, just log
        \"""
        logging.info('Hello logsense')


    if __name__ == '__main__':
        # Initialize tracer
        setup_tracer(logsense_token='Your very own logsense token')

        # Run application
        with opentracing.tracer.start_active_span('hello'):
            hello_logsense()

        # Tracer should be finished explicitly, because of multithreading approach
        wait_on_tracer()

Description of `opentracing.tracer.start_active_span` is available in further reading.

`setup_tracer` and `wait_on_tracer` are just below
"""
import os
import logging
import opentracing
import time

from logsense.sender import LogSenseSender
from logsense_opentracing.tracer import Tracer
from logsense_opentracing.handler import OpentracingLogsenseHandler

def setup_tracer(logsense_token=None, logger=None, sender=None, component=None):
    """
    Setups tracer with all required informations.

    It connects to the logger, so all further logs will be send to the logsense server

    It should be called as soon as possible in your main application code.

    To do it, just call::

        from logsense_opentracing.utils import setup_tracer
        setup_tracer(logsense_token='Your very own logsense token')

    :arg logsense_token: your own personal token in UUID format.
    :arg logger: logger name. All logs logged by this logger will be pushed to the logsense platform.
    :arg sender: You can use your own sender

    Return:
        * `opentracing.Tracer` - tracer instantion. It's already saved as `opentracing.tracer`,
          so no need to use it directly
    """
    log = logging.getLogger(logger)  # pylint: disable=invalid-name
    log.addHandler(OpentracingLogsenseHandler())
    log.setLevel(logging.DEBUG)

    level = os.getenv('LOGSENSE_LOG_LEVEL', 'INFO').upper()

    if level in ('CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG'):
        level = getattr(logging, level)
    else:
        level = logging.INFO

    # Do not propagate logsense.opentracing logger
    logsense_log = logging.getLogger('logsense.opentracing')
    logsense_log.propagate = False
    logsense_log.setLevel(level)
    logsense_log_handler = logging.StreamHandler()
    logsense_log_formatter = logging.Formatter('%(asctime)s [%(levelname)-8s]: [lgsns-ot] %(message)s')
    logsense_log_formatter.converter = time.gmtime
    logsense_log_handler.setFormatter(logsense_log_formatter)
    logsense_log.addHandler(logsense_log_handler)

    logsense_token = os.getenv('LOGSENSE_TOKEN', logsense_token)  # pylint: disable=unused-variable

    sender = LogSenseSender(logsense_token) if sender is None else sender

    tracer = Tracer(sender=sender, component=component)  # pylint: disable=invalid-name
    opentracing.tracer = tracer
    return tracer

def wait_on_tracer():
    """
    Since this project communicates with logsense on the other thread.
    `wait_on_tracer` should be called to ensure that everything was sent correctly. which should be se

    Return:
        * None
    """
    opentracing.tracer.finish()
