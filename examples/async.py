# pylint: disable=missing-docstring,duplicate-code
import logging
import random
import time
import asyncio
import opentracing

from logsense_opentracing.tracer import Tracer


log = logging.getLogger()  # pylint: disable=invalid-name
tracer = Tracer()  # pylint: disable=invalid-name
opentracing.tracer = tracer
ioloop = asyncio.get_event_loop()  # pylint: disable=invalid-name

async def finish():
    opentracing.tracer.finish()
    ioloop.stop()

async def app():
    with opentracing.tracer.start_active_span('parent-span') as scope:
        scope.span.set_tag('appname', 'async')
        scope.span.set_tag('event', 'true')
        time.sleep(random.randint(1, 3))
        with opentracing.tracer.start_active_span('child-span', child_of=scope) as new_scope:
            time.sleep(random.randint(1, 3))
            new_scope.span.log_kv({
                'message': 'Log from child-span',
                'relation': 'child'
            })
        time.sleep(random.randint(1, 3))
        scope.span.log_kv({
            'message': 'Log from parent-span',
            'relation': 'parent'
        })
    asyncio.ensure_future(finish())

asyncio.ensure_future(app())
ioloop.run_forever()
