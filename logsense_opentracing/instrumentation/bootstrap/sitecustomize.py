import os
import sys
from logsense_opentracing.utils import setup_tracer
from logsense_opentracing.instrumentation import patch_module, ALL_ARGS


def process():
    filepath = os.path.abspath(sys.argv[0])
    app = sys.argv[0].lstrip("./").replace(os.path.sep, '.')

    if app.endswith('.py'):
        app = app[:-3]
    path_name = os.path.abspath(os.path.dirname(__file__))
    sys.path.append(path_name)
    sys.path.append(os.getcwd())

    setup_tracer()
    patch_module(app)


if hasattr(sys, 'argv'):
    process()
else:
    # if sys.argv doesn't exist yet,
    # assign object with overwritten destructor to it
    class PatchModule:
        def __del__(self):
            process()

    sys.argv = PatchModule()
