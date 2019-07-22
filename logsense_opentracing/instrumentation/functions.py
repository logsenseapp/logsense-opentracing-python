"""
Patching function is an easy as just using patch_single and patch_async_single functions

Synchronous example::

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

Asynchronous example::

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

Be aware that for decorators, you should use decorators module

"""
import logging

from .utils import get_obj_from_path
from .general import instrumentation, async_instrumentation


log = logging.getLogger('logsense.opentracing.instrumentation')  # pylint: disable=invalid-name


def patch_single(module, **kwargs):
    """
    Automatically override target module to use instrumentation.
    See `instrumentation` function for details about `kwargs`

    :param module: Module path to patch
    :type module: `str`
    """
    log.info('Patching function %s', module)

    path, name, old_function = get_obj_from_path(module)

    patched_function = instrumentation(
        old_function,
        **kwargs
        )

    setattr(path, name, patched_function)
    return patched_function


async def patch_async_single(module, **kwargs):
    """
    Automatically override target module to use instrumentation.
    See `instrumentation` function for details about `kwargs` params

    :param module: Module path to patch
    :type module: `str`
    """
    log.info('Patching async function %s', module)

    path, name, old_function = get_obj_from_path(module)

    setattr(path, name, await async_instrumentation(
        old_function,
        **kwargs
        ))
