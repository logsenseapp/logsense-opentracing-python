"""
Instrumentation module provides useful functions for automatic instrumentation
throught the opentracing
"""
import importlib
import inspect
import opentracing
from flask import request


def instrumentation(inside_function, before=None):
    """
    Wraps `inside_function` as opentracing span
    """
    def new_func(*args, **kwargs):
        operation_name = '{0}.{1}'.format(
            inside_function.__module__,
            inside_function.__name__
        )

        with opentracing.tracer.start_active_span(operation_name) as scope:

            # Run `before` hook
            if before is not None:
                before(scope, *args, **kwargs)

            # get list of and default arguments
            function_defaults = inside_function.__defaults__ or []
            function_args = inspect.getfullargspec(inside_function)[0]

            # set default arguments
            for name, value in zip(reversed(function_args), reversed(function_defaults)):
                scope.span.set_tag('kwarg.{0}'.format(name), str(value))

            # override arguments by args
            for name, value in zip(function_args, args):
                scope.span.set_tag('kwarg.{0}'.format(name), str(value))

            # override arguments by kwargs
            for name, value in kwargs.items():
                scope.span.set_tag('kwarg.{0}'.format(name), str(value))

            # execute function
            return inside_function(*args, **kwargs)
    return new_func


def _decorator_instrumentation(func, before=None):
    def new_decorator(*args, **kwargs):
        """
        This is function which originally is executed to generate decorator
        """
        decorator = func(*args, **kwargs)

        def new_inside_function(inside_function):
            return decorator(instrumentation(inside_function, before=before))
        return new_inside_function

    return new_decorator


def patch_single(module, before=None):
    """
    Patch single module with `func`. It automatically override target module to use instrumentation.
    It's not suit for decorators now
    """
    paths = module.split('.')
    mod = importlib.import_module(paths[0])
    for i in range(1, len(paths)-1):
        mod = getattr(mod, paths[i])
    setattr(mod, paths[-1], instrumentation(getattr(mod, paths[-1]), before=before))


def patch_decorator(module, before=None):
    """
    Patch single decorator module with `func`. It automatically override targetmodule
    to use instrumentation.
    It's not suit for decorators now
    """
    paths = module.split('.')
    mod = importlib.import_module(paths[0])
    for i in range(1, len(paths)-1):
        mod = getattr(mod, paths[i])
    setattr(mod, paths[-1], _decorator_instrumentation(getattr(mod, paths[-1]), before=before))


def flask_route(scope, *args, **kwargs):  # pylint: disable=unused-argument
    """
    Extract information from flask request and put into opentracing scope
    """
    scope.span.set_tag('http.url', request.url)
    scope.span.set_tag('http.method', request.method)
    scope.span.set_tag('peer.ipv4', request.remote_addr)
