import importlib
ALL_ARGS = object()

HTTP_SPAN_ID = 'ot-tracer-spanid'
HTTP_TRACE_ID = 'ot-tracer-traceid'
HTTP_BAGGAGE_PREFIX = 'ot-baggage-'


def get_obj_from_path(module):
    """
    Obtain module path, function name and function basing on module string
    """
    paths = module.split('.')
    mod = importlib.import_module(paths[0])

    for i in range(1, len(paths)-1):
        mod = getattr(mod, paths[i])

    return mod, paths[-1], getattr(mod, paths[-1])

