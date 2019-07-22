"""
Experimental functionality!

Module patching is experimental, because it can affect all module at once and should be used carefully
"""
import logging
import importlib
import inspect
import asyncio

from .functions import patch_single, patch_async_single


log = logging.getLogger('logsense.opentracing.instrumentation')  # pylint: disable=invalid-name


def patch_module(module, recursive=True, include_paths=None, exclude_paths=None):
    """
    Experimental (patch module)

    :param module: Module path to be patched
    :type module: ``str```
    :param recursive: Patch module recursively if True, otherwise module's functions only
    :type recursive: ``bool``
    :param include_paths: Tuple of path regexes which should be patched. Matches all if tuple is empty
    :type include_paths: ``bool``
    :param exclude_paths: Tuple of path regexes which shouldn't be patched
    :typ exclude_paths: ``bool``

    """
    log.warning('Patching module is an experimental feature')
    log.info('Patching module %s', module)

    include_paths = () if include_paths is None else include_paths
    exclude_paths = () if exclude_paths is None else exclude_paths

    # Import module and skip builtins
    paths = module.split('.')
    if paths[0] in ('builtins', ):
        return

    mod = importlib.import_module(paths[0])
    try:
        for i in range(1, len(paths)):
            mod = getattr(mod, paths[i])
    except Exception as exception:  # pylint: disable=broad-except
        log.warning('Exception during importing module %s', exception)

    # Iterate over all methods
    for function in dir(mod):
        # Skip f method is not an attribute
        if not hasattr(mod, function):
            log.debug('%s is not module %s attribute', function, module)
            continue

        # Skip all dunderscore methods
        if function.startswith('__'):
            continue

        current = getattr(mod, function)

        # Skip already patched modules
        if hasattr(current, '_logsense_patched'):
            continue

        # Obtain import paths of given attribute. Method depends on type of attribute
        # For module use __name__
        if inspect.ismodule(current):
            new_path = current.__name__
        elif inspect.isfunction(current):
            # Skip dunderscore functions
            if current.__name__.startswith('__'):
                continue
            # For method use mod's __module__, __name__ and attribute's __name__
            if inspect.isclass(mod):
                new_path = '{}.{}.{}'.format(mod.__module__, mod.__name__, current.__name__)
            # For function use __module__ and __name__
            else:
                new_path = '{}.{}'.format(current.__module__, current.__name__)
        # For class use __module__ and __name__
        elif inspect.isclass(current):
            new_path = '{}.{}'.format(current.__module__, current.__name__)
        # Other types are unsupported
        else:
            log.warning('Cannot classify %s:%s. Skipping', module, function)
            continue

        # Skip all modules which aren't part of mod
        if not new_path.startswith(module):
            log.debug('%s is not in %s module. Skipping', new_path, module)
            continue

        log.debug('Trying to patch %s', new_path)

        # Allow paths if there is no allowed paths
        allow = not include_paths

        for allowed in include_paths:
            if new_path.startswith(allowed):
                allow = True
                break

        for denied in exclude_paths:
            if new_path.startswith(denied):
                allow = False

        if not allow:
            log.info('Path %s is excluded from patching. Skipping', new_path)
            continue

        # Patch coroutines with coroutines
        if inspect.iscoroutinefunction(current):
            log.debug('Patching async function %s', new_path)
            loop = asyncio.get_event_loop()
            loop.run_until_complete(patch_async_single(new_path))
        # Patch function witch function patcher
        elif inspect.isfunction(current):
            log.debug('Patching function %s', new_path)
            patch_single(new_path)
        # Patch modules recursively, if recursive is enabled
        elif inspect.ismodule(current):
            if recursive is True:
                log.debug('Patching module %s', new_path)
                patch_module(new_path, recursive=recursive, include_paths=include_paths, exclude_paths=exclude_paths)
        # Treat classes as packages
        elif inspect.isclass(current):
            log.info('Patching class %s', current)
            patch_module(new_path, recursive=recursive, include_paths=include_paths, exclude_paths=exclude_paths)
