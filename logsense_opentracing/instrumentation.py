"""
Instrumentation module provides useful functions for automatic instrumentation
throught the opentracing
"""
import importlib
import inspect
import opentracing


def instrumentation(inside_function, before=None, after=None, arguments=None):
    """
    Wraps `inside_function` as opentracing span
    """
    arguments = arguments if arguments is not None else []
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
                if name in arguments:
                    scope.span.set_tag('kwarg.{0}'.format(name), str(value))

            # override arguments by args
            for name, value in zip(function_args, args):
                if name in arguments:
                    scope.span.set_tag('kwarg.{0}'.format(name), str(value))

            # override arguments by kwargs
            for name, value in kwargs.items():
                if name in arguments:
                    scope.span.set_tag('kwarg.{0}'.format(name), str(value))

            # execute function
            scope.span.set_tag('error', False)
            try:
                result = inside_function(*args, **kwargs)

                # Run `after` hook
                if after is not None:
                    after(scope, result, error=False, *args, **kwargs)

                # return result
                return result
            except Exception as exception:
                scope.span.set_tag('error', True)

                # Run `after` hook
                if after is not None:
                    after(scope, result, error=True, *args, **kwargs)

                # pass inside_function execution exception
                raise exception
    return new_func


async def async_instrumentation(inside_function, before=None, arguments=None):
    """
    Wraps `inside_function` as opentracing span.
    Exactly same as function above, but in async version
    """
    arguments = arguments if arguments is not None else []
    async def new_func(*args, **kwargs):
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
                if name in arguments:
                    scope.span.set_tag('kwarg.{0}'.format(name), str(value))

            # override arguments by args
            for name, value in zip(function_args, args):
                if name in arguments:
                    scope.span.set_tag('kwarg.{0}'.format(name), str(value))

            # override arguments by kwargs
            for name, value in kwargs.items():
                if name in arguments:
                    scope.span.set_tag('kwarg.{0}'.format(name), str(value))

            # execute function
            scope.span.set_tag('error', False)
            try:
                return await inside_function(*args, **kwargs)
            except Exception as exception:
                scope.span.set_tag('error', True)
                raise exception
    return new_func


def _decorator_instrumentation(func, before=None, arguments=None):
    def new_decorator(*args, **kwargs):
        """
        This is function which originally is executed to generate decorator
        """
        decorator = func(*args, **kwargs)

        def new_inside_function(inside_function):
            return decorator(instrumentation(
                inside_function,
                before=before,
                arguments=arguments
                ))
        return new_inside_function

    return new_decorator


async def _async_decorator_instrumentation(func, before=None, arguments=None):
    async def new_decorator(*args, **kwargs):
        """
        This is function which originally is executed to generate decorator
        Exactly same as function above, but in async version
        """
        decorator = await func(*args, **kwargs)

        async def new_inside_function(inside_function):
            return decorator(
                await async_instrumentation(
                    inside_function,
                    before=before,
                    arguments=arguments
                    ))
        return new_inside_function

    return new_decorator


def patch_single(module, arguments=None, before=None):
    """
    Patch single module with `func`. It automatically override target module to use instrumentation.
    For decorators use patch_decorator
    """
    paths = module.split('.')
    mod = importlib.import_module(paths[0])
    for i in range(1, len(paths)-1):
        mod = getattr(mod, paths[i])
    setattr(mod, paths[-1], instrumentation(
        getattr(mod, paths[-1]),
        before=before,
        arguments=arguments
        ))


async def patch_async_single(module, arguments=None, before=None):
    """
    Patch single module with `func`. It automatically override target module to use instrumentation.
    For decorator use patch_async_decorator
    Exactly same as function above, but in async version
    """
    paths = module.split('.')
    mod = importlib.import_module(paths[0])
    for i in range(1, len(paths)-1):
        mod = getattr(mod, paths[i])
    setattr(mod, paths[-1], await async_instrumentation(
        getattr(mod, paths[-1]),
        before=before,
        arguments=arguments
        ))


def patch_decorator(module, arguments=None, before=None):
    """
    Patch single decorator module with `func`. It automatically override target module
    to use instrumentation.
    It's usable only for decorators
    """
    paths = module.split('.')
    mod = importlib.import_module(paths[0])
    for i in range(1, len(paths)-1):
        mod = getattr(mod, paths[i])
    setattr(mod, paths[-1], _decorator_instrumentation(
        getattr(mod, paths[-1]),
        before=before,
        arguments=arguments
        ))


async def patch_async_decorator(module, arguments=None, before=None):
    """
    Patch single decorator module with `func`. It automatically override target module
    to use instrumentation.
    It's usable only for decorators
    Exactly same as function above, but in async version
    """
    paths = module.split('.')
    mod = importlib.import_module(paths[0])
    for i in range(1, len(paths)-1):
        mod = getattr(mod, paths[i])
    setattr(mod, paths[-1], await _async_decorator_instrumentation(
        getattr(mod, paths[-1]),
        before=before,
        arguments=arguments
        ))


def flask_route(scope, *args, **kwargs):  # pylint: disable=unused-argument
    """
    Extract information from flask request and put into opentracing scope
    """
    from flask import request  # Optional import

    scope.span.set_tag('http.url', request.url)
    scope.span.set_tag('http.method', request.method)
    scope.span.set_tag('peer.ipv4', request.remote_addr)
