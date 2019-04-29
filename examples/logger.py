"""
This example shows how to use logging with opentracing and logsense
"""
import logging
import opentracing

from logsense_opentracing.tracer import Tracer
from logsense_opentracing.handler import OpentracingLogsenseHandler

log = logging.getLogger()  # pylint: disable=invalid-name
log.addHandler(OpentracingLogsenseHandler())
log.setLevel(logging.DEBUG)

tracer = Tracer()  # pylint: disable=invalid-name
opentracing.tracer = tracer

with opentracing.tracer.start_active_span('first') as first:
    log.info('Aloha 1')
    with opentracing.tracer.start_active_span('second', child_of=first) as second:
        log.info({
            'content': 'Aloha 2'
        })
        with opentracing.tracer.start_active_span('third', child_of=second):
            log.warning('Be aware of good weather!!!')

opentracing.tracer.finish()
