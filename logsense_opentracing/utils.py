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
        setup_tracer(logsense_token='Your very own logsense token', dummy_sender=True)

        # Run application
        with opentracing.tracer.start_active_span('hello'):
            hello_logsense()

        # Tracer should be finished explicitly, because of multithreading approach
        wait_on_tracer()

Description of `opentracing.tracer.start_active_span` is available in further reading.

`setup_tracer` and `wait_on_tracer` are just below
"""
import logging
import opentracing

from logsense_opentracing.tracer import Tracer
from logsense_opentracing.handler import OpentracingLogsenseHandler

def setup_tracer(logsense_token, logger=None, dummy_sender=False):
    """
    Setups tracer with all required informations.

    It connects to the logger, so all further logs will be send to the logsense server

    It should be called as soon as possible in your main application code.

    To do it, just call::

        from logsense_opentracing.utils import setup_tracer
        setup_tracer(logsense_token='Your very own logsense token', dummy_sender=True)

    :arg logsense_token: your own personal token in UUID format.
    :arg logger: logger name. All logs logged by this logger will be pushed to the logsense platform.
    :arg dummy_sender: for testing purposes.
        Set it to True to see what will be send without actually sending it.

    Return:
        * `opentracing.Tracer` - tracer instantion. It's already saved as `opentracing.tracer`,
          so no need to use it directly
    """
    log = logging.getLogger(logger)  # pylint: disable=invalid-name
    log.addHandler(OpentracingLogsenseHandler())
    log.setLevel(logging.DEBUG)

    # Do not propagate logsense.opentracing logger
    logsense_log = logging.getLogger('logsense.opentracing')
    logsense_log.propagate = False

    tracer = Tracer(logsense_token=logsense_token, dummy_sender=dummy_sender)  # pylint: disable=invalid-name
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
