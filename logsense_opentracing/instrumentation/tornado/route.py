import logging
import opentracing
from ..utils import HTTP_TRACE_ID, HTTP_SPAN_ID, HTTP_BAGGAGE_PREFIX


log = logging.getLogger('logsense.opentracing')  # pylint: disable=invalid-name


def tornado_route(scope, *args, **kwargs):
    handler = args[0]

    # Extract trace if available
    carrier = {
        'baggage': {}
    }

    if handler.request.headers.get(HTTP_TRACE_ID):
        try:
            carrier['trace_id'] = int(handler.request.headers[HTTP_TRACE_ID], 16)
        except ValueError:
            log.warning('Incorrect header value: %s', handler.request.headers[HTTP_TRACE_ID])

    if handler.request.headers.get(HTTP_SPAN_ID):
        try:
            carrier['span_id'] = int(handler.request.headers[HTTP_SPAN_ID], 16)
        except ValueError:
            log.warning('Incorrect header value: %s', handler.request.headers[HTTP_SPAN_ID])

    prefix_len = len(HTTP_BAGGAGE_PREFIX)

    for name, value in handler.request.headers.items():
        if name.startswith(HTTP_BAGGAGE_PREFIX) and name != HTTP_BAGGAGE_PREFIX:
            carrier[name[prefix_len:]] = value

    try:
        opentracing.tracer.extract(opentracing.propagation.Format.TEXT_MAP, carrier)
    except Exception as exception:  # pylint: disable=broad-except
        log.warning(exception)

    # Extract request information
    scope.span.set_tag('http.url', handler.request.full_url())
    scope.span.set_tag('http.method', handler.request.method)
    scope.span.set_tag('peer.ipv4', handler.request.remote_ip)

    return args, kwargs
