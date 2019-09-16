"""
General instrumentation functions
"""
import logging
import inspect

import opentracing

from .utils import get_obj_from_path
from .utils import ALL_ARGS


log = logging.getLogger('logsense.opentracing.instrumentation')  # pylint: disable=invalid-name


def instrumentation(function, **kwargs):
    """
    Instrument given function

    :param function: Function to instrument
    :type function: ``callable``

    :returns: Wrapped function

    """
    # If function is already instrumented, just returns it
    if hasattr(function, '_logsense_patched'):
        log.debug('%s already patched', function)
        return function

    # Patch function and set atributes
    result_function = _instrumentation(function=function, **kwargs)
    setattr(result_function, '_logsense_original_function', function)
    setattr(result_function, '_logsense_patched', True)
    return result_function


def remove_instrumentation(module):
    """
    Remove instrumentation from given module

    :param module: Module path
    :type module: ``str``

    :returns: Original unwrapped function
    """
    path, name, current_function = get_obj_from_path(module)

    if not hasattr(current_function, '_logsense_patched'):
        return current_function

    original_function = getattr(current_function, '_logsense_original_function')
    setattr(path, name, original_function)

    return original_function


def _instrumentation(function, before=None, after=None, arguments=None):
    """
    Wraps `function` as opentracing span

    :param function: Function which is going to be patched
    :type function: ``callable``
    :param before: Function which is going to be run before executing function. It's executed in tracer scope
    :type before: ``callable``
    :param after: Function which is going to be run after executing function.
        It's executed in tracer scope. It's called even if function throw exception
    :type after: ``callable``
    :param arguments: Arguments which are going to be reported to the opentracing server.
        ALL_ARGS for reporting all arguments
    :type arguments: ``list``

    This function is internal and shouldn't be call outside of the module

    """
    arguments = arguments if arguments is not None else []
    def new_func(*args, **kwargs):
        operation_name = '{0}.{1}'.format(
            function.__module__,
            function.__name__
        )

        with opentracing.tracer.start_active_span(operation_name) as scope:

            # Run `before` hook
            if before is not None:
                try:
                    args, kwargs = before(scope, *args, **kwargs)
                except Exception as exception:  # pylint: disable=broad-except
                    log.warning(exception)

            # get list of and default arguments
            function_defaults = function.__defaults__ or []
            function_args = inspect.getfullargspec(function)[0]

            # set default arguments
            for name, value in zip(reversed(function_args), reversed(function_defaults)):
                if arguments is ALL_ARGS or name in arguments:
                    scope.span.set_tag('kwarg.{0}'.format(name), str(value))

            # override arguments by args
            # Iterate from end, because it works incorrectly for static method
            for name, value in zip(reversed(function_args), reversed(args)):
                if arguments is ALL_ARGS or name in arguments:
                    scope.span.set_tag('kwarg.{0}'.format(name), str(value))

            # override arguments by kwargs
            for name, value in kwargs.items():
                if arguments is ALL_ARGS or name in arguments:
                    scope.span.set_tag('kwarg.{0}'.format(name), str(value))

            # execute function
            scope.span.set_tag('error', False)

            # skip self if method is static
            # ToDo: Improve checking if method is static or not
            if len(args) + len(kwargs) == len(function_args) + 1:
                args = args[1:]

            # Should be class method, remove first argument
            if function_args and function_args[0] == 'cls':
                args = args[1:]

            try:
                result = function(*args, **kwargs)

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

                # pass function execution exception
                raise exception
    return new_func

async def async_instrumentation(function, **kwargs):
    """
    Instrument given async function

    :param function: Function to instrument
    :type function: ``coroutine``

    """
    # If function is already instrumented, just returns it
    if hasattr(function, '_logsense_patched'):
        log.debug('%s already patched', function)
        return function

    # Patch function and set atributes
    result_function = await _async_instrumentation(function=function, **kwargs)
    setattr(result_function, '_logsense_original_function', function)
    setattr(result_function, '_logsense_patched', True)
    return result_function

async def _async_instrumentation(function, before=None, arguments=None):
    """
    Wraps `function` as opentracing span

    :param function: Function which is going to be patched
    :type function: ``callable``
    :param before: Function which is going to be run before executing function. It's executed in tracer scope
    :type before: ``callable``
    :param after: Function which is going to be run after executing function.
        It's executed in tracer scope. It's called even if function throw exception
    :type after: ``callable``
    :param arguments: Arguments which are going to be reported to the opentracing server.
        ALL_ARGS for reporting all arguments
    :type arguments: ``list``

    This function is internal and shouldn't be call outside of the module
    """
    arguments = arguments if arguments is not None else []
    async def new_func(*args, **kwargs):
        operation_name = '{0}.{1}'.format(
            function.__module__,
            function.__name__
        )

        with opentracing.tracer.start_active_span(operation_name) as scope:

            # Run `before` hook
            if before is not None:
                before(scope, *args, **kwargs)

            # get list of and default arguments
            function_defaults = function.__defaults__ or []
            function_args = inspect.getfullargspec(function)[0]

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
                return await function(*args, **kwargs)
            except Exception as exception:
                scope.span.set_tag('error', True)
                raise exception
    return new_func
