"""
This example shows how to use logging with opentracing and logsense
"""
import logging
import opentracing

from logsense_opentracing.tracer import Tracer
from logsense_opentracing.handler import OpentracingLogsenseHandler
from logsense_opentracing.utils import setup_tracer


# Initialize tracer
setup_tracer(component='logger')

with opentracing.tracer.start_active_span('first') as first:
    logging.info('Aloha 1')
    with opentracing.tracer.start_active_span('second', child_of=first) as second:
        logging.info({
            'content': 'Aloha 2'
        })
        with opentracing.tracer.start_active_span('third', child_of=second):
            logging.warning('Be aware of good weather!!!')

opentracing.tracer.finish()
