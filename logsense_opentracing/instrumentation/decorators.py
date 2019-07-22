"""
Decorators are treaten in special way. We consider two kinds of decorators:

    * Flat decorator - shouldn't be executed and always is use like that::

        @decorator
        def function():
            ...

    * Non-flat decorator - should be always called and looks like that::

        @decorator(...)
        def function():
            ...

For now we don't have clear idea how to aumatically recognize way the decorator is used, so we separated it as above

Depending on what you can achive, you can instrument only original function or both decorator and function.
`decoratod_only` parameter is useful for that

Below are some examples of instrumentation of sync, async, flat, no-flat decorators

Sync flat decorator example::

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

Sync non-flat decorator example::

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

Async flat decorator example::

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

Async non-flat decorator example::

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
import logging
import functools

from .utils import get_obj_from_path
from .general import instrumentation, async_instrumentation


log = logging.getLogger('logsense.opentracing.instrumentation')  # pylint: disable=invalid-name


def _build_decorator(decorator, only_decorated, **kwargs):
    """
    Build decorator

    :param decorator: Decorator which is base for returned decorator
    :type decorator: ``callable`
    :param only_decorated: Decorate only function if True, otherwise decorator which function
    :type only_decorated: ``bool``
    """
    def new_decorator(decorated_function):
        if only_decorated is True:
            return decorator(instrumentation(
                decorated_function,
                **kwargs
                ))

        return instrumentation(
            decorator(decorated_function),
            **kwargs
            )

    return new_decorator


def _build_async_decorator(decorator, only_decorated, **kwargs):
    """
    Build async decorator

    :param decorator: Decorator which is base for returned decorator
    :type decorator: ``callable`
    :param only_decorated: Decorate only function if True, otherwise decorator which function
    :type only_decorated: ``bool``
    """
    def flat_decorator(decorated_function):

        @functools.wraps(flat_decorator)
        async def new_decorator(*argz, **kwargz):
            if only_decorated is True:
                return await decorator(await async_instrumentation(
                    decorated_function,
                    **kwargs
                    ))(*argz, **kwargz)

            return await (await async_instrumentation(
                decorator(decorated_function),
                **kwargs
                ))(*argz, **kwargz)

        return new_decorator

    return flat_decorator


def _decorator_instrumentation(decorator, flat=False, **kwargs):
    """
    :param decorator: Decorator to be wrapped
    :type decorator: ``callable``
    :param flat: True if decorator is flat, False otherwise.
    :type flat: `bool`

    """
    flat_decorator = _build_decorator(
        decorator=decorator,
        **kwargs
        )

    def non_flat_decorator(*argz, **kwargz):
        return _build_decorator(
            decorator=decorator(*argz, **kwargz),
            **kwargs
        )

    if flat is True:
        return flat_decorator

    return non_flat_decorator


def _async_decorator_instrumentation(decorator, flat=False, **kwargs):
    """
    :param decorator: Decorator to be wrapped
    :type decorator: ``str``
    :param flat: True if decorator is flat, False otherwise.
    :type flat: ``bool``
    """
    flat_decorator = _build_async_decorator(
        decorator=decorator,
        **kwargs
        )

    def non_flat_decorator(*argz, **kwargz):
        return _build_async_decorator(
            decorator=decorator(*argz, **kwargz),
            **kwargs
            )

    if flat is True:
        return flat_decorator

    return non_flat_decorator

def patch_decorator(module, **kwargs):
    """
    Automatically override target decorator to use instrumentation.
    See `instrumentation` function for details about `arguments` and `before`

    :param module: Decorator to override
    :type module: ``str``

    """
    path, name, old_function = get_obj_from_path(module)

    setattr(path, name, _decorator_instrumentation(
        old_function,
        **kwargs
        ))


def patch_async_decorator(decorator, **kwargs):
    r"""
    Patch single async decorator with `func`. It automatically overrides target decorator
    to use instrumentation.
    It's usable only for async decorators
    The same as patch_decorator function, but in async version

    :param decorator: Path of decorator to be wrapped
    :type decorator: ``str``
    :param \**kwargs: `_async_decorator_instrumentation` kwargs
    """
    path, name, old_function = get_obj_from_path(decorator)

    setattr(path, name, _async_decorator_instrumentation(
        old_function,
        **kwargs
        ))
