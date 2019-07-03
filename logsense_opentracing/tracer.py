"""
Opentracing's Tracer implementation.

More details:
https://opentracing-python.readthedocs.io/en/latest/api.html#opentracing.Tracer
"""

import time
import random
import os
import json
from queue import Queue, Empty
from threading import Lock, Thread
import opentracing

from .span import Span
from .scope import Scope
from .span_context import SpanContext
from .scope_manager import ScopeManager


class _DummySender:
    def __init__(*args, **kwargs):  # pylint: disable=no-method-argument
        pass

    def close(*args, **kwargs):  # pylint: disable=no-method-argument
        pass

    def emit_with_time(self, label, timestamp, data):
        print('{} {} {}'.format(timestamp, label, json.dumps(data, indent=4)))


class Tracer(opentracing.Tracer):
    """
    Implements opentracing.Tracer
    """
    _supported_formats = [opentracing.propagation.Format.TEXT_MAP]

    def __init__(self, scope_manager=None, sender=None):
        super().__init__(scope_manager=scope_manager)

        self._scope_manager = ScopeManager()  if scope_manager is None else scope_manager
        self.random = random.Random(time.time() * (os.getpid() or 1))

        self._queue = Queue()
        self._lock = Lock()

        self._sender = sender

        self._thread = Thread(target=self.process)
        self._thread.start()

    def start_active_span(self,  # pylint: disable=too-many-arguments
                          operation_name,
                          child_of=None,
                          references=None,
                          tags=None,
                          start_time=None,
                          ignore_active_span=False,
                          finish_on_close=True,
                          component=None):

        # Get parent's scope from arguments or by scope manager otherwise
        parent = child_of if child_of is not None else self._scope_manager.active

        # Assign trace_id from parent's scope or generate it if scope doesn't exist
        trace_id = parent.span.context.trace_id if parent is not None else self._random_id()

        span = Span(tracer=self, context=SpanContext(
            span_id=self._random_id(),
            trace_id=trace_id,
            baggage=parent.span.context.baggage if parent is not None else None,
            parent=parent
            ))
        span.set_tag('operation_name', operation_name)
        span.set_tag('component', component if component is not None else operation_name)

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

    def extract(self, format, carrier):  # pylint: disable=redefined-builtin
        active_context = self.active_span.context

        if format != opentracing.propagation.Format.TEXT_MAP:
            raise opentracing.propagation.UnsupportedFormatException(format)

        mandatory_keys = {'trace_id', 'baggage'}
        keys_difference = mandatory_keys - set(carrier.keys())
        if keys_difference:
            error_msg = 'Carrier incomplete. Lack of few keys: {keys}'.format(keys=keys_difference)
            raise ValueError(error_msg)

        active_context.trace_id = str(carrier['trace_id'])

        for key, value in carrier['baggage'].items():
            active_context.set_baggage(key, value)

        return active_context

    def inject(self, span_context, format, carrier):  # pylint: disable=redefined-builtin
        if format != opentracing.propagation.Format.TEXT_MAP:
            raise opentracing.propagation.UnsupportedFormatException(format)

        if isinstance(span_context, Span):
            # be flexible and allow Span as argument, not only SpanContext
            span_context = span_context.context

        if not isinstance(span_context, SpanContext):
            raise ValueError('Expecting SpanContext, not {}'.format(type(span_context)))

        carrier['baggage'] = {}
        carrier['trace_id'] = span_context.trace_id
        carrier['span_id'] = span_context.span_id

        for key, value in span_context.items():
            carrier[key] = value

        return span_context
