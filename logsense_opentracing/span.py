"""
Opentracing's Span implementation.

More details:
https://opentracing-python.readthedocs.io/en/latest/api.html#opentracing.Span
"""

import time
import opentracing


class Span(opentracing.Span):
    """
    Implements opentracing.Span
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
    def duration_us(self):
        """
        Get span duration in microseconds
        """
        if self._duration is None:
            return None

        return int(self._duration * 1e6)

    def set_tag(self, key, value):
        self._tags[key] = value

    def log_kv(self, key_values, timestamp=None):
        timestamp = time.time() if timestamp is None else timestamp
        self._logs.append({
            'timestamp': timestamp,
            'log': key_values
        })

    def finish(self, finish_time=None):
        self._end_timestamp = time.time()
        self._duration = self._end_timestamp - self._start_timestamp

        self.tracer.put_to_queue(self)

    def get_data(self) -> dict:
        """
        Data which should be send to the logsense client
        """
        return_value = []

        for log in self._logs:
            data = log['log']
            data.update(self._tags)
            data.update(self.context.data)
            data.update({
                'duration_us': self.duration_us,
                'time_position_us': round((log['timestamp'] - self._start_timestamp) * 1e6)
            })

            return_value.append({
                'label': 'opentracing',
                'timestamp': log['timestamp'],
                'data': data
            })

        return return_value


    def set_baggage_item(self, key, value):
        self.context.set_baggage(key, value)
        return self

    def get_baggage_item(self, key):
        return self.context.baggage.get(key)
