"""
Logsense opentracer comes with some handy functions for minimize amount of work
and understanding of opentracing.

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

`setup_tracer` and `wait_on_tracer` are described on this page
"""
import os
import logging
import time
import opentracing

from logsense.sender import LogSenseSender
from logsense_opentracing.tracer import Tracer
from logsense_opentracing.tracer import _DummySender, DataDogSender
from logsense_opentracing.handler import OpentracingLogsenseHandler

def setup_tracer(logsense_token=None, logger=None, sender=None, component=None):
    """
    Setups tracer with all required informations.

    It connects to the logger, so all further logs will be send to the logsense server

    It should be called as soon as possible in your main application code.

    To do it, just call::

        from logsense_opentracing.utils import setup_tracer
        setup_tracer(logsense_token='Your very own logsense token')

    You could use your own sender and send logs wherever you want, but we would be very unhappy if you do it :(

    :param logsense_token: Your own personal token in UUID format. It's override by `LOGSENSE_TOKEN` environmental
        variable if it exists. To get your token go to `logsense.com <https://www.logsense.com/>`_.
    :param logger: Logger name. All logs logged by this logger are going to be pushed to the logsense platform via
        sender
    :param sender: You can use your own sender, but as it was mentioned before, it makes us a saaad pandaaa
    :param component: Component name. In other words, it's your application name. It's used to track source of logs

    Envs:
        * LOGSENSE_TOKEN - overrides `logsense_token`
        * LOGSENSE_LOG_LEVEL - logging level of logsense internal logs.
          It can take `critical`, `error`, `warning`, `info`, `debug` as value

    :returns: `opentracing.Tracer` - tracer instantion. It's already saved as `opentracing.tracer`,
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

    if logsense_token is not None:
        sender = LogSenseSender(logsense_token)
    elif os.getenv('DD_ENABLED') is not None:
        sender = DataDogSender()
    else:
        sender = _DummySender()

    logsense_log.info('Using %s for sending logs', type(sender))

    tracer = Tracer(sender=sender, component=component)  # pylint: disable=invalid-name
    opentracing.tracer = tracer
    return tracer

def wait_on_tracer():
    """
    Since this project communicates with logsense on the other thread,
    `wait_on_tracer` should be called to ensure that everything was sent correctly.
    This function should be called always before closing application

    """
    opentracing.tracer.finish()
