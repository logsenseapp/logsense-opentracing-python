"""
Opentracing's ScopeManager implementation.

More details:
https://opentracing-python.readthedocs.io/en/latest/api.html#opentracing.ScopeManager
"""

import inspect
import opentracing

from .scope import Scope


class ScopeManager(opentracing.ScopeManager):
    """
    Implements opentracing.ScopeManager
    """
    STACK_DEPTH = 100

    def activate(self, span, finish_on_close):
        """Makes a :class:`Span` active.

        :param span: the :class:`Span` that should become active.
        :param finish_on_close: whether :class:`Span` should be automatically
            finished when :meth:`Scope.close()` is called.

        :rtype: Scope
        :return: a :class:`Scope` to control the end of the active period for
            *span*. It is a programming error to neglect to call
            :meth:`Scope.close()` on the returned instance.
        """
        parent_frame = inspect.stack()[2][0]
        scope = Scope(self, span)
        parent_frame.f_locals['logsense_opentracing_scope'] = scope
        return scope


    @property
    def active(self):
        stack = inspect.stack()
        old_scope = None
        for frame in range(2, min(len(stack), self.STACK_DEPTH)):
            local_variables = stack[frame][0].f_locals
            old_scope = local_variables.get('logsense_opentracing_scope', None)
            if old_scope is None:
                continue

            return old_scope

        return None
