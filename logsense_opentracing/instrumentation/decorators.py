import logging
import importlib
import inspect
import asyncio
import functools
import opentracing

from .functions import patch_single, patch_async_single
from .utils import get_obj_from_path
from .general import instrumentation, async_instrumentation


log = logging.getLogger('logsense.opentracing.instrumentation')


def _decorator_instrumentation(decorator, before=None, arguments=None, flat=False, alternative=False):
    """
    :arg decorator: Decorator to be wrapped
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

    def non_flat_decorator(*args, **kwargs):
        executed_decorator = decorator(*args, **kwargs)

        def non_flat_decorator(decorated_function):
            if alternative is True:
                return executed_decorator(instrumentation(
                    decorated_function,
                    before=before,
                    arguments=arguments
                ))
            else:
                return instrumentation(
                    executed_decorator(decorated_function),
                    before=before,
                    arguments=arguments
                )

        return non_flat_decorator

    if flat is True:
        return flat_decorator
    else:
        return non_flat_decorator


def _async_decorator_instrumentation(decorator, before=None, arguments=None, flat=False, only_decorated=False):
    """
    :arg decorator: Decorator to be wrapped
    :arg before: See instrumentation
    :arg arguments: See instrumentation
    :arg flat: True if decorator is flat, False otherwise.
    :arg only_decorated: see `_decorator_instrumentation: alternative`
    """
    def flat_decorator(decorated_function):

        @functools.wraps(flat_decorator)
        async def new_decorator(*args, **kwargs):
            if only_decorated is True:
                return await decorator(await async_instrumentation(
                    decorated_function,
                    before=before,
                    arguments=arguments
                    ))(*args, **kwargs)
            else:
                return await (await async_instrumentation(
                    decorator(decorated_function),
                    before=before,
                    arguments=arguments
                    ))(*args, **kwargs)

        return new_decorator

    def non_flat_decorator(*args, **kwargs):
        executed_decorator = decorator(*args, **kwargs)

        def non_flat_decorator(decorated_function):
            @functools.wraps(non_flat_decorator)
            async def new_decorator(*args, **kwargs):
                if only_decorated is True:
                    return await (executed_decorator(await async_instrumentation(
                        decorated_function,
                        before=before,
                        arguments=arguments
                        )))(*args, **kwargs)
                else:
                    return await (await async_instrumentation(
                        executed_decorator(decorated_function),
                        before=before,
                        arguments=arguments
                        ))(*args, **kwargs)

            return new_decorator

        return non_flat_decorator

    if flat is True:
        return flat_decorator
    else:
        return non_flat_decorator

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
    path, name, old_function = get_obj_from_path(module)

    setattr(path, name, _decorator_instrumentation(
        old_function,
        before=before,
        arguments=arguments,
        flat=flat,
        alternative=alternative
        ))


def patch_async_decorator(module, arguments=None, before=None, flat=False, only_decorated=False):
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
    path, name, old_function = get_obj_from_path(module)

    setattr(path, name, _async_decorator_instrumentation(
        old_function,
        before=before,
        arguments=arguments,
        flat=flat,
        only_decorated=only_decorated
        ))

