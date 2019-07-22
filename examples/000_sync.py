# pylint: disable=missing-docstring
import random
import time
import opentracing

from logsense_opentracing.utils import setup_tracer


# Initialize tracer
setup_tracer(component='sync')


with opentracing.tracer.start_active_span('parent-span') as scope:

    # Set some tags
    scope.span.set_tag('app_name', 'sync_app')
    scope.span.set_tag('event', 'true')

    for _ in range(5):
        time.sleep(random.randint(1, 3))
        # Create child span as child of parent-span
        with opentracing.tracer.start_active_span(
            'child-span', child_of=scope) as new_scope:
            time.sleep(random.randint(1, 3))

            # Log from child span
            new_scope.span.log_kv({
                'message': 'Log from child-span',
                'relation': 'child'
            })

        time.sleep(random.randint(1, 3))
        # Log from parent span
        scope.span.log_kv({
            'message': 'Log from parent-span',
            'relation': 'parent'
        })

# Wait for all logs to be send
opentracing.tracer.finish()
