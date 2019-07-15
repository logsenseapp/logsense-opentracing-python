
import logging
import inspect

import opentracing

from .utils import get_obj_from_path
from .utils import ALL_ARGS


log = logging.getLogger('logsense.opentracing.instrumentation')  # pylint: disable=invalid-name


def instrumentation(inside_function, before=None, after=None, arguments=None):
    # If function is already instrumented, just returns it
    if hasattr(inside_function, '_logsense_patched'):
        log.debug('%s already patched', inside_function)
        return inside_function

    # Patch function and set atributes
    result_function = _instrumentation(inside_function=inside_function, before=before, after=after, arguments=arguments)
    setattr(result_function, '_logsense_original_function', inside_function)
    setattr(result_function, '_logsense_patched', True)
    return result_function


def remove_instrumentation(module):
    path, name, current_function = get_obj_from_path(module)

    if not hasattr(current_function, '_logsense_patched'):
        return current_function

    original_function = getattr(current_function, '_logsense_original_function')
    setattr(path, name, original_function)

    return original_function


def _instrumentation(inside_function, before=None, after=None, arguments=None):
    """
    Wraps `inside_function` as opentracing span

    :arg inside_function: Function which is going to be patched
    :arg before: Function which is going to be run before executing function. It's executed in tracer scope
    :arg after: Function which is going to be run after executing function.
        It's executed in tracer scope. It's called even if inside_function throw exception
    :arg arguments: Arguments which are going to be reported to the opentracing server.
        ALL_ARGS for reporting all arguments

    This function is internal and shouldn't be call outside of the module

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
                try:
                    args, kwargs = before(scope, *args, **kwargs)
                except Exception as exception:  # pylint: disable=broad-except
                    log.warning(exception)

            # get list of and default arguments
            function_defaults = inside_function.__defaults__ or []
            function_args = inspect.getfullargspec(inside_function)[0]

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
    The same as instrumentation function, but in async version
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
