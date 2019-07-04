"""
Instrumentation module provides useful functions for automatic instrumentation
through the opentracing

Because of lack of ideas how to handle all decorators by one function they are separated on two types:

* Flat - when decorator is not callable while using, it's consider as flat decorator
* Non-Flat - if decorator takes argument before generating final decorator it's considered as non-flat decorator

Please keep it in mind while using, because it can lead to the some issues

"""
import logging
import functools
import importlib
import inspect
import opentracing
import types

log = logging.getLogger('logsense_opentracing.instrumentation')

ALL_ARGS = object()

def instrumentation(inside_function, before=None, after=None, arguments=None):
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
                    before(scope, *args, **kwargs)
                except Exception as exception:
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
            if len(function_args) > 0 and function_args[0] == 'cls':
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


def _decorator_instrumentation(func, before=None, arguments=None, flat=False, alternative=False):
    """
    :arg func: Decorator to be wrapped
    :arg before: See instrumentation
    :arg arguments: See instrumentation
    :arg flat: True if decorator is flat, False otherwise.
    :arg alternative: The decorated function is wrapped by instrumentation if alternative is True,
        otherwise decorator is wrapped by instrumentation.

        Let's see whats the result of flat decorator:

        with alternative equals False (default behaviour)::

            instrumentation(decorator(function))

        with alternative equals True::

            decorator(instrumentation(function))

    """
    def flat_decorator(decorated_function):
        if alternative is True:
            return func(instrumentation(
                decorated_function,
                before=before,
                arguments=arguments
                ))
        else:
            return instrumentation(
                func(decorated_function),
                before=before,
                arguments=arguments
                )

    def non_flat_decorator(*args, **kwargs):
        decorator = func(*args, **kwargs)

        def non_flat_decorator(decorated_function):
            if alternative is True:
                return decorator(instrumentation(
                    decorated_function,
                    before=before,
                    arguments=arguments
                ))
            else:
                return instrumentation(
                    decorator(decorated_function),
                    before=before,
                    arguments=arguments
                )

        return non_flat_decorator


    if flat is True:
        return flat_decorator
    else:
        return non_flat_decorator


def _async_decorator_instrumentation(func, before=None, arguments=None, flat=False):
    """
    :arg func: Decorator to be wrapped
    :arg before: See instrumentation
    :arg arguments: See instrumentation
    :arg flat: True if decorator is flat, False otherwise.
    """
    def flat_decorator(decorated_function):
        @functools.wraps(flat_decorator)
        async def new_decorator(*args, **kwargs):
            operation_name = '{0}.{1}'.format(
                decorated_function.__module__,
                decorated_function.__name__
            )
            with opentracing.tracer.start_active_span(operation_name) as scope:
                return await (instrumentation(
                    func,
                    before=before,
                    arguments=arguments
                    )(decorated_function))(*args, **kwargs)

        return new_decorator

    def non_flat_decorator(*args, **kwargs):
        decorator = func(*args, **kwargs)

        def non_flat_decorator(decorated_function):
            @functools.wraps(non_flat_decorator)
            async def new_decorator(*args, **kwargs):
                operation_name = '{0}.{1}'.format(
                    decorated_function.__module__,
                    decorated_function.__name__
                )
                with opentracing.tracer.start_active_span(operation_name) as scope:
                    return await (instrumentation(
                        decorator,
                        before=before,
                        arguments=arguments
                        )(decorated_function))(*args, **kwargs)

            return new_decorator

        return non_flat_decorator

    if flat is True:
        return flat_decorator
    else:
        return non_flat_decorator


def patch_single(module, arguments=None, before=None):
    """
    Automatically override target module to use instrumentation.
    See `instrumentation` function for details about `arguments` and `before`

    :arg module: Module to override
    :arg arguments: See instrumentation
    :arg before: See instrumentation

    Consider simple example::

        from requests import get
        from logsense_opentracing.tracer import Tracer
        from logsense_opentracing.instrumentation import patch_single

        def foo():
            print('bar')
            get('https://logsense.com')

        if __name__ == '__main__':
            # Initialize tracer
            tracer = Tracer(logsense_token='Your very own logsense token')
            opentracing.tracer = tracer

            # Patch functions to use opentracing
            patch_single('__main__.foo')
            patch_single('requests.get)

            # Run application
            foo()

    For decorators use patch_decorator
    """
    paths = module.split('.')
    mod = importlib.import_module(paths[0])
    for i in range(1, len(paths)-1):
        mod = getattr(mod, paths[i])

    patched_function = instrumentation(
        getattr(mod, paths[-1]),
        before=before,
        arguments=arguments
        )
    setattr(mod, paths[-1], patched_function)
    return patched_function


async def patch_async_single(module, arguments=None, before=None):
    """
    Automatically override target module to use instrumentation.
    See `instrumentation` function for details about `arguments` and `before`

    :arg module: Module to override
    :arg arguments: See instrumentation
    :arg before: See instrumentation

    Consider simple example::

        from asyncio import get_event_loop
        from logsense_opentracing.tracer import Tracer
        from logsense_opentracing.instrumentation import patch_async_single

        async def foo():
            print('bar')

        if __name__ == '__main__':
            # Initialize tracer
            tracer = Tracer(logsense_token='Your very own logsense token')
            opentracing.tracer = tracer

            # Patch functions to use opentracing
            patch_async_single('__main__.foo')

            # Run application
            get_event_loop().run_until_complete(foo())

    For decorators use patch_async_decorator
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


def patch_decorator(module, arguments=None, before=None, flat=False, alternative=False):
    """
    Automatically override target decorator to use instrumentation.
    See `instrumentation` function for details about `arguments` and `before`

    :arg module: Decorator to override
    :arg arguments: See instrumentation
    :arg before: See instrumentation
    :arg flat: Set flat as True if decorator is not callable.
        Not callable means, it's used `@decorator` instead of `@decorator(...)`.

        **Decorators which supports both behaviors are not supported,**
        **so you have to use `@decorator(...)` for them and flat=False**
    :arg alternative:

    Flat decorator example::

        import logging
        from logsense_opentracing.utils import setup_tracer, wait_on_tracer
        from logsense_opentracing.instrumentation import patch_decorator


        # Define or import decorators (it should be done before patching)
        def flat_decorator(function):
            def decorated_function(*args, **kwargs):
                logging.info('Before executing function as flat')
                result = function(*args, **kwargs)
                logging.info('After executing function as flat')
                return result

            return decorated_function

        # Decorator should be patched before using it.
        patch_decorator('__main__.flat_decorator', flat=True)


        # Use decorators
        @flat_decorator
        def hello_flat_world():
            logging.info('Our world is flat')


        if __name__ == '__main__':
            # Initialize tracer
            setup_tracer(logsense_token='Your very own logsense token')

            # Run application
            hello_flat_world()

            # Tracer should be finished explicit, because of multithreading approach
            wait_on_tracer()

    Non-flat decorator example::

        import logging
        from logsense_opentracing.utils import setup_tracer, wait_on_tracer
        from logsense_opentracing.instrumentation import patch_decorator


        # Define or import decorators (it should be done before patching)
        def non_flat_decorator(first, second):
            def decorator(function):
                def decorated_function(*args, **kwargs):
                    logging.info('First parameter is %s', first)
                    result = function(*args, **kwargs)
                    logging.info('Second parameter is %s', second)
                    return result

                return decorated_function
            return decorator

        # Decorator should be patched before using it.
        patch_decorator('__main__.non_flat_decorator')


        # Use decorators
        @non_flat_decorator(1, 17)
        def hello_sphere_world():
            logging.info('Our world is sphere')


        if __name__ == '__main__':
            # Initialize tracer
            setup_tracer(logsense_token='Your very own logsense token')

            # Run application
            hello_sphere_world()

            # Tracer should be finished explicit, because of multithreading approach
            wait_on_tracer()

    For ordinary functions use patch_single
    """
    paths = module.split('.')
    mod = importlib.import_module(paths[0])
    for i in range(1, len(paths)-1):
        mod = getattr(mod, paths[i])
    setattr(mod, paths[-1], _decorator_instrumentation(
        getattr(mod, paths[-1]),
        before=before,
        arguments=arguments,
        flat=flat,
        alternative=alternative
        ))


def patch_async_decorator(module, arguments=None, before=None, flat=False):
    """
    Patch single decorator module with `func`. It automatically override target module
    to use instrumentation.
    It's usable only for decorators
    The same as patch_decorator function, but in async version

    Flat decorator example::

        import logging
        import functools
        from asyncio import get_event_loop
        from logsense_opentracing.utils import setup_tracer, wait_on_tracer
        from logsense_opentracing.instrumentation import patch_async_decorator


        # Define or import decorators (it should be done before patching)
        def flat_decorator(function):
            @functools.wraps(function)
            async def decorated_function(*args, **kwargs):
                logging.info('Before executing function as flat')
                result = await function(*args, **kwargs)
                logging.info('After executing function as flat')
                return result

            return decorated_function

        # Decorator should be patched before using it.
        patch_async_decorator('__main__.flat_decorator', flat=True)


        # Use decorators
        @flat_decorator
        async def hello_flat_world():
            logging.info('Our world is flat')


        if __name__ == '__main__':
            # Initialize tracer
            setup_tracer(logsense_token='Your very own logsense token')

            # Run application
            get_event_loop().run_until_complete(hello_flat_world())

            # Tracer should be finished explicit, because of multithreading approach
            wait_on_tracer()

    Non-flat decorator example::

        import logging
        import functools
        from asyncio import get_event_loop
        from logsense_opentracing.utils import setup_tracer, wait_on_tracer
        from logsense_opentracing.instrumentation import patch_async_decorator


        # Define or import decorators (it should be done before patching)
        def non_flat_decorator(first, second):
            def decorator(function):
                @functools.wraps(function)
                async def decorated_function(*args, **kwargs):
                    logging.info('First parameter is %s', first)
                    result = function(*args, **kwargs)
                    logging.info('Second parameter is %s', second)
                    return result

                return decorated_function
            return decorator

        # Decorator should be patched before using it.
        patch_async_decorator('__main__.non_flat_decorator', flat=False)


        # Use decorators
        @non_flat_decorator(1, 17)
        def hello_sphere_world():
            logging.info('Our world is sphere')


        if __name__ == '__main__':
            # Initialize tracer
            setup_tracer(logsense_token='Your very own logsense token')

            # Run application
            get_event_loop().run_until_complete(hello_sphere_world())

            # Tracer should be finished explicit, because of multithreading approach
            wait_on_tracer()
    """
    paths = module.split('.')
    mod = importlib.import_module(paths[0])
    for i in range(1, len(paths)-1):
        mod = getattr(mod, paths[i])
    setattr(mod, paths[-1], _async_decorator_instrumentation(
        getattr(mod, paths[-1]),
        before=before,
        arguments=arguments,
        flat=flat
        ))


def flask_route(scope, *args, **kwargs):  # pylint: disable=unused-argument
    """
    Extract information from flask request and put into opentracing scope

    ::

        import logging
        import asyncio
        from flask import Flask
        import opentracing

        from logsense_opentracing.tracer import Tracer
        from logsense_opentracing.instrumentation import patch_decorator, flask_route
        from logsense_opentracing.utils import setup_tracer


        app = Flask('hello-flask')

        # Initialize tracer
        setup_tracer(logsense_token='your own personal token')

        # Decorator should be patched before using it.
        patch_decorator('flask.Flask.route', before=flask_route, flat=False, alternative=True)

        # Define routing
        @app.route("/sayHello/<name>")
        def say_hello(name):
            import logging
            logging.info('User %s entered', name)
            return 'Hello {}'.format(name)


        # Run application
        if __name__ == "__main__":
            app.run(port=8080)
    """
    from flask import request  # Optional import

    # Extract trace if available
    carrier = {}

    if request.headers.get('logsense-trace-id'):
        carrier['trace_id'] = request.headers['logsense-trace-id']

    if 'logsense-baggage' in request.headers:
        carrier['baggage'] = dict(
            data.split('=') for data in request.headers['logsense-baggage'].split(',')
            )

    try:
        opentracing.tracer.extract(opentracing.propagation.Format.TEXT_MAP, carrier)
    except Exception as exception:
        log.warning(exception)

    # Extract request information
    scope.span.set_tag('http.url', request.url)
    scope.span.set_tag('http.method', request.method)
    scope.span.set_tag('peer.ipv4', request.remote_addr)


def patch_module(module, recursive=True, include_paths=None, exclude_path=''):
    """
    Experimental


    """
    # Import module and skip builtins
    paths = module.split('.')
    if paths[0] in ('builtins', ):
        return

    mod = importlib.import_module(paths[0])
    for i in range(1, len(paths)):
        mod = getattr(mod, paths[i])


    # Iterate over all methods
    for function in dir(mod):
        # Skip f method is not an attribute
        if not hasattr(mod, function):
            continue

        # Skip all dunderscore methods
        if function.startswith('__'):
            continue

        current = getattr(mod, function)

        if not hasattr(current, '__module__'):
            # Skip all root level modules
            continue

        # Skip already patched modules
        if hasattr(current, '_logsense_patched'):
            continue

        try:
            setattr(current, '_logsense_patched', True)
        except AttributeError:
            # Skip all methods for which cannot set patching flag
            continue

        new_path = '{}.{}'.format('.'.join(paths), function)

        if paths[0] != current.__module__.split('.')[0]:
            # Use module path instead of current path
            new_path = '{}.{}'.format(current.__module__, current.__name__)

        if inspect.isfunction(current):
            log.info('Patching function %s', new_path)
            patch_single(new_path)
        elif inspect.ismodule(current):
            # currently do nothing, Will back here with new ideas
            pass
        elif inspect.isclass(current):
            for path in include_paths if include_paths is not None else []:
                if current.__module__.startswith(path):
                    log.info('Patching module %s', current)
                    patch_module(new_path, recursive=True, include_paths=include_paths, exclude_path=exclude_path)
