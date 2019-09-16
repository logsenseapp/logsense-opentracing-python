"""
Logsense opentracing utils. Helpers for manipulating modules paths
"""
import logging
import importlib
import opentracing


ALL_ARGS = object()

HTTP_SPAN_ID = 'ot-tracer-spanid'
HTTP_TRACE_ID = 'ot-tracer-traceid'
HTTP_BAGGAGE_PREFIX = 'ot-baggage-'
HTTP_BAGGAGE_PREFIX_LEN = len(HTTP_BAGGAGE_PREFIX)


log = logging.getLogger('logsense.opentracing')  # pylint: disable=invalid-name


def get_obj_from_path(module):
    """
    Obtain module path, function name and function basing on module string

    :param module: Module path
    :type module: ``str``

    :returns tuple: Tuple of module path which contains function, function name and function itself
    """
    paths = module.split('.')
    mod = importlib.import_module(paths[0])

    for i in range(1, len(paths)-1):
        mod = getattr(mod, paths[i])

    return mod, paths[-1], getattr(mod, paths[-1])


def extract_http_carrier(headers):
    """
    Extract baggage from given dictionary of HTTP headers

    :param headers: HTTP headers container
    :type headers: ``dict``

    :returns: Carrier dictionary
    """
    # Extract trace if available
    carrier = {
        'baggage': {}
    }

    if headers.get(HTTP_TRACE_ID):
        try:
            carrier['trace_id'] = int(headers[HTTP_TRACE_ID], 16)
        except ValueError:
            log.warning('Incorrect header value: %s', headers[HTTP_TRACE_ID])

    if headers.get(HTTP_SPAN_ID):
        try:
            carrier['span_id'] = int(headers[HTTP_SPAN_ID], 16)
        except ValueError:
            log.warning('Incorrect header value: %s', headers[HTTP_SPAN_ID])

    for name, value in headers.items():
        if name.startswith(HTTP_BAGGAGE_PREFIX) and name != HTTP_BAGGAGE_PREFIX:
            carrier[name[HTTP_BAGGAGE_PREFIX_LEN:]] = value

    try:
        opentracing.tracer.extract(opentracing.propagation.Format.TEXT_MAP, carrier)
    except Exception as exception:  # pylint: disable=broad-except
        log.warning(exception)

    return carrier
