from time import sleep
import json

class Record:

    def __init__(self, timestamp, label, data):
        self._timestamp = timestamp
        self._label = label
        self._data = data

    def __str__(self):
        return json.dumps({
            'timestamp': self._timestamp,
            'label': self._label,
            'data': self.data
        })

    @property
    def data(self):
        return self._data


class MockSender:
    def __init__(self, *args, **kwargs):  # pylint: disable=no-method-argument
        self.data = []

    def close(*args, **kwargs):  # pylint: disable=no-method-argument
        pass

    def emit_with_time(self, label, timestamp, data):
        self.data.append(Record(timestamp=timestamp, label=label, data=data))

    def wait_on_data(self):
        while not self.data:
            sleep(0.1)

    def get_data(self):
        return self.data
