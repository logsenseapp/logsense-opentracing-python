"""
Opentracing's Scope implementation.

More details:
https://opentracing-python.readthedocs.io/en/latest/api.html#opentracing.Scope
"""

import opentracing


class Scope(opentracing.Scope):
    """
    Implements opentracing.Scope
    """

    def close(self):
        self._span.finish()
