# pylint: disable=missing-docstring
import logging
import opentracing

from logsense_opentracing.tracer import Tracer
from logsense_opentracing.utils import setup_tracer


# Initialize tracer
setup_tracer(component='baggage')

with opentracing.tracer.start_active_span('parent-span') as scope:
    scope.span.set_baggage_item('greeting', 'Aloha!')
    with opentracing.tracer.start_active_span('child-span', child_of=scope) as new_scope:
        print(new_scope.span.get_baggage_item('greeting'), ' :)')

opentracing.tracer.finish()
