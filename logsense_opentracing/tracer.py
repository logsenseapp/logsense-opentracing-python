"""
Opentracing's Tracer implementation.

More details:
https://opentracing-python.readthedocs.io/en/latest/api.html#opentracing.Tracer
"""

import time
import random
import os
from queue import Queue, Empty
from threading import Lock, Thread
import opentracing
from logsense.sender import LogSenseSender
from fluent.sender import EventTime

from .span import Span
from .scope import Scope
from .span_context import SpanContext
from .scope_manager import ScopeManager


class Tracer(opentracing.Tracer):
    """
    Implements opentracing.Tracer
    """

    def __init__(self, scope_manager=None):
        super().__init__(scope_manager=scope_manager)

        self._scope_manager = ScopeManager()  if scope_manager is None else scope_manager
        self.random = random.Random(time.time() * (os.getpid() or 1))
        logsense_token = os.getenv('LOGSENSE_TOKEN')  # pylint: disable=unused-variable

        self._queue = Queue()
        self._lock = Lock()

        self._sender = LogSenseSender(logsense_token)

        self._thread = Thread(target=self.process)
        self._thread.start()

    def start_active_span(self,  # pylint: disable=too-many-arguments
                          operation_name,
                          child_of=None,
                          references=None,
                          tags=None,
                          start_time=None,
                          ignore_active_span=False,
                          finish_on_close=True):

        # Get parent's scope from arguments or by scope manager otherwise
        parent = child_of if child_of is not None else self._scope_manager.active

        # Assign trace_id from parent's scope or generate it if scope doesn't exist
        trace_id = parent.span.context.trace_id if parent is not None else self._random_id()

        span = Span(tracer=self, context=SpanContext(
            span_id=self._random_id(),
            trace_id=trace_id
            ))
        span.set_tag('operation_name', operation_name)

        self._scope_manager.activate(span, finish_on_close=True)
        scope = Scope(self._scope_manager, span)
        return scope

    def _random_id(self):
        return self.random.getrandbits(64)

    def put_to_queue(self, span):
        """
        Put span to sending queue
        """

        with self._lock:
            self._queue.put(span)

    def process(self):
        """
        Process logs queue (should be run as separated thread)
        """

        while True:
            try:
                with self._lock:
                    span = self._queue.get(block=False)
                    if span is None:
                        self._sender.close()
                        return

                for data in span.get_data():
                    self._sender.emit_with_time(
                        label=data['label'],
                        timestamp=data['timestamp'],
                        data=data['data']
                        )
            except Empty:
                time.sleep(0.5)

    def finish(self):
        """
        Finish sender thread
        """
        self._queue.put(None)
