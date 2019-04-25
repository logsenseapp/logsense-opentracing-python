"""
Opentracing's SpanContext implementation.

More details:
https://opentracing-python.readthedocs.io/en/latest/api.html#opentracing.SpanContext
"""

import opentracing


class SpanContext(opentracing.SpanContext):
    """
    Implements opentracing.SpanContext
    """

    __slots__ = ['trace_id', 'span_id']

    def __init__(self,
                 trace_id,
                 span_id,
                 baggage=None):
        self.trace_id = trace_id
        self.span_id = span_id
        self._baggage = baggage or opentracing.SpanContext.EMPTY_BAGGAGE

    @property
    def baggage(self):
        return self._baggage or opentracing.SpanContext.EMPTY_BAGGAGE

    @property
    def data(self) -> dict:
        """
        Data which should be sent to the opentracing server
        """
        return {
            'trace_id': self.trace_id,
            'span_id': self.span_id
        }
