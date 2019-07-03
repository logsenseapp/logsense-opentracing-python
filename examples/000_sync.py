# pylint: disable=missing-docstring
import logging
import random
import time
import opentracing

from logsense_opentracing.utils import setup_tracer
from logsense_opentracing.tracer import Tracer


# Initialize tracer
# setup_tracer(logsense_token='6bfd7d2f-7d45-414a-899d-f85175b08980', dummy_sender=False)
setup_tracer(logsense_token='a0ca3c77-5f27-4b17-802d-bd7f6895b1f8', dummy_sender=False)


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
