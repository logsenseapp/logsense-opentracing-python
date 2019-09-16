# pylint: disable=missing-docstring,duplicate-code
import logging
import random
import time
import asyncio
import opentracing

from logsense_opentracing.utils import setup_tracer
from logsense_opentracing.tracer import Tracer


# Initialize tracer
setup_tracer(component='async')

ioloop = asyncio.get_event_loop()  # pylint: disable=invalid-name

async def finish():
    # Ensure all logs were sent correctly
    opentracing.tracer.finish()
    ioloop.stop()

async def app():
    # Create parent span
    with opentracing.tracer.start_active_span('parent-span') as scope:
        scope.span.set_tag('app_name', 'async')
        scope.span.set_tag('event', 'true')

        await asyncio.sleep(random.randint(1, 3))

        # Create child span as child of parent-span
        with opentracing.tracer.start_active_span(
            'child-span', child_of=scope) as new_scope:

            await asyncio.sleep(random.randint(1, 3))

            # Log from child span
            new_scope.span.log_kv({
                'message': 'Log from child-span',
                'relation': 'child'
            })

        await asyncio.sleep(random.randint(1, 3))
        # Log from parent span
        scope.span.log_kv({
            'message': 'Log from parent-span',
            'relation': 'parent'
        })
    asyncio.ensure_future(finish())

asyncio.ensure_future(app())
ioloop.run_forever()
