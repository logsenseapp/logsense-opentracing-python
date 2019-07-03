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
                 baggage=None,
                 parent=None):
        self.trace_id = trace_id
        self.span_id = span_id
        self._baggage = baggage or opentracing.SpanContext.EMPTY_BAGGAGE
        self._parent = parent

    @property
    def baggage(self):
        return self._baggage

    def set_baggage(self, key, value):
        """
        Set baggage `key` as `value`
        """
        self._baggage[key] = value

    @property
    def data(self) -> dict:
        """
        Data which should be sent to the opentracing server
        """
        return_value = {
            'trace_id': self.trace_id,
            'span_id': self.span_id
        }

        if self._parent is not None:
            return_value['parent_span_id'] = self._parent.span.context.span_id

        return return_value
