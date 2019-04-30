# pylint: disable=missing-docstring
import logging
import opentracing

from logsense_opentracing.tracer import Tracer


log = logging.getLogger()  # pylint: disable=invalid-name
tracer = Tracer()  # pylint: disable=invalid-name
opentracing.tracer = tracer

with opentracing.tracer.start_active_span('parent-span') as scope:
    scope.span.context.set_baggage('greeting', 'Aloha!')
    with opentracing.tracer.start_active_span('child-span', child_of=scope) as new_scope:
        print(new_scope.span.context.baggage.get('greeting'), ' :)')

opentracing.tracer.finish()
