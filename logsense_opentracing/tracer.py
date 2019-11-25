"""
Opentracing's Tracer implementation.

More details:
https://opentracing-python.readthedocs.io/en/latest/api.html#opentracing.Tracer
"""

import time
import random
import os
import json
import logging
import threading
from queue import Queue, Empty
from threading import Lock, Thread
import opentracing

from .span import Span
from .scope import Scope
from .span_context import SpanContext
from .scope_manager import ScopeManager


log = logging.getLogger('logsense.opentracing.tracer')  # pylint: disable=invalid-name


class _DummySender:
    def __init__(*args, **kwargs):  # pylint: disable=no-method-argument
        pass

    def close(*args, **kwargs):  # pylint: disable=no-method-argument,missing-docstring
        pass

    def emit_with_time(self, label, timestamp, data):  # pylint: disable=missing-docstring,no-self-use
        print('{} {} {}'.format(timestamp, label, json.dumps(data, indent=4)))


class Tracer(opentracing.Tracer):
    """
    Implements opentracing.Tracer
    """
    _supported_formats = [opentracing.propagation.Format.TEXT_MAP]

    def __init__(self, scope_manager=None, sender=None, component=None):
        super().__init__(scope_manager=scope_manager)

        self._scope_manager = ScopeManager()  if scope_manager is None else scope_manager
        self.random = random.Random(time.time() * (os.getpid() or 1))

        self._queue = Queue()
        self._lock = Lock()

        self._sender = sender

        self._thread = Thread(target=self.process)
        self._thread.start()
        self._component = component

    def start_active_span(self,  # pylint: disable=too-many-arguments,arguments-differ
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
        span.set_tag('component', component if component is not None else \
                                  self._component if self._component is not None else \
                                  operation_name)

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
        main_thread_exited = False

        while True:
            if not main_thread_exited and not threading.main_thread().is_alive():
                log.info("%s exited", threading.main_thread().name)
                main_thread_exited = True
                self.finish()

            try:
                with self._lock:
                    span = self._queue.get(block=False)
                    if span is None:
                        self._sender.close()
                        log.info("Processing has been finished")
                        return

                for data in span.get_data():
                    self._sender.emit_with_time(
                        label=data['label'],
                        timestamp=data['timestamp'],
                        data=data['data']
                        )
            except Empty:
                time.sleep(0.1)

    def finish(self):
        """
        Finish sender thread
        """
        self._queue.put(None)

    def extract(self, format, carrier):  # pylint: disable=redefined-builtin
        active_context = self.active_span.context

        if format != opentracing.propagation.Format.TEXT_MAP:
            raise opentracing.propagation.UnsupportedFormatException(format)

        mandatory_keys = {'trace_id', 'baggage', 'span_id'}
        keys_difference = mandatory_keys - set(carrier.keys())
        if keys_difference:
            log.debug('Carrier incomplete. Lack of few keys: %s', keys_difference)
            return active_context

        active_context.trace_id = str(carrier['trace_id'])

        # Create fake scope just to be parent scope
        # ToDO: Improve parent managing. Aim is to avoid this hack
        active_context._parent = Scope(
            self._scope_manager,
            span=Span(
                tracer=self,
                context=SpanContext(
                    span_id=str(carrier['span_id']),
                    trace_id=active_context.trace_id,
                    baggage=carrier['baggage'] or None
                    )))

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
        carrier['trace_id'] = str(span_context.trace_id)
        carrier['span_id'] = str(span_context.span_id)

        for key, value in span_context.baggage.items():
            carrier['baggage'][key] = value

        return span_context
