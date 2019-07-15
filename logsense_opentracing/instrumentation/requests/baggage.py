import opentracing
from ..utils import HTTP_TRACE_ID, HTTP_SPAN_ID, HTTP_BAGGAGE_PREFIX

def requests_baggage(scope, method, url, **kwargs):
    if kwargs.get('headers') is None:
        kwargs['headers'] = {}

    baggage = {}

    opentracing.tracer.inject(scope.span, opentracing.propagation.Format.TEXT_MAP, baggage)

    kwargs['headers'][HTTP_TRACE_ID] = hex(int(baggage['trace_id']))[2:]  # strip '0x'
    kwargs['headers'][HTTP_SPAN_ID] = hex(int(baggage['span_id']))[2:]
    for key, value in baggage['baggage'].items():
        kwargs['headers']['{}{}'.format(HTTP_BAGGAGE_PREFIX, key)] = value

    return (method, url), kwargs
