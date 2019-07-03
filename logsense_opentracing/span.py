"""
Opentracing's Span implementation.

`Opentracing documentation <https://opentracing-python.readthedocs.io/en/latest/api.html#opentracing.Span>`_

To use logsense opentracing implementation you should use at least one span.
There is not any automagic created main span

To create your span, you can use this snippet::

    import opentracing

    ...

    with opentracing.tracer.start_active_span('hello'):
        ...

You saw this code already. It creates new span with name `hello`.
This name is using in logsense to track place of application your logs comes from,
so should be as meaningful for you as possible
"""

import time
import opentracing


class Span(opentracing.Span):
    """
    Implements `opentracing.Span <https://opentracing-python.readthedocs.io/en/latest/api.html#opentracing.Span>`_
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._tags = {}
        self._start_timestamp = time.time()
        self._logs = [{
            'timestamp': self._start_timestamp,
            'log': {}
        }]  # Initialize logs with empty log (for span purposes)
        self._end_timestamp = None
        self._duration = None

    @property
    def _duration_us(self):
        """
        Get span duration in microseconds
        """
        if self._duration is None:
            return None

        return int(self._duration * 1e6)

    def set_tag(self, key, value):
        """
        Set tag to given value
        """
        self._tags[key] = value

    def log_kv(self, key_values, timestamp=None):
        """
        Send structured logs from this span via logger
        """
        timestamp = time.time() if timestamp is None else timestamp
        self._logs.append({
            'timestamp': timestamp,
            'log': key_values
        })

    def finish(self, finish_time=None):
        """
        Called at the end of span
        """
        self._end_timestamp = time.time()
        self._duration = self._end_timestamp - self._start_timestamp

        self.tracer.put_to_queue(self)

    def _prefix_keys(self, data):
        return {'ot.{}'.format(key): value for key, value in data.items()}

    def get_data(self) -> dict:
        """
        Data which should be send to the logsense client
        """
        return_value = []

        for log in self._logs:
            data = log['log']
            _type = 'trace' if log['log'] == {} else 'python'
            data.update(self._prefix_keys(self._tags))
            data.update(self._prefix_keys(self.context.data))
            data.update(self._prefix_keys({
                'duration_us': self._duration_us,
                'time_position_us': round((log['timestamp'] - self._start_timestamp) * 1e6)
            }))

            data['_type'] = _type

            return_value.append({
                'label': 'opentracing',
                'timestamp': log['timestamp'],
                'data': data
            })

        return return_value


    def set_baggage_item(self, key, value):
        """
        Set baggage item. Useful for inter-application tracing
        """
        self.context.set_baggage(key, value)
        return self

    def get_baggage_item(self, key):
        """
        Get baggage item value
        """
        return self.context.baggage.get(key)
