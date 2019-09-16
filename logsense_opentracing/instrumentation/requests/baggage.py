"""
`Requests <https://pypi.org/project/requests/>`_ integration
"""
import opentracing
from ..utils import HTTP_TRACE_ID, HTTP_SPAN_ID, HTTP_BAGGAGE_PREFIX


def requests_baggage(scope, method, url, **kwargs):
    r"""
    Function which injects opentracing into requests HTTP carrier.
    It takes same parameters as `requests.api.request`,
    modify it and calls `requests.api.request` with modified parameters

    ::

        \"\"\"
        Run `nc -lp 8888` in linux console to see which headers was send exactly
        \"\"\"
        import logging
        import requests
        import tornado.ioloop
        import tornado.web
        import opentracing

        from logsense_opentracing.utils import setup_tracer
        from logsense_opentracing.instrumentation import patch_single, tornado_route, requests_baggage, patch_module

        # Initialize tracer
        setup_tracer(component='Requests')
        patch_single('requests.api.request', before=requests_baggage)

        with opentracing.tracer.start_active_span('parent-span') as scope:
            scope.span.set_baggage_item('suitcase', 'My docs with important information')
            requests.get('http://localhost:8888/', headers={'my-header': 'I\'m using opentracing'})

    :param scope: Opentracing's scope
    :type scope: ``opentracing.Scope``
    :param method: Requests' method
    :param url: Requests' url
    :param \**kwarg: Requests' kwargs
    """
    if kwargs.get('headers') is None:
        kwargs['headers'] = {}

    baggage = {}

    opentracing.tracer.inject(scope.span, opentracing.propagation.Format.TEXT_MAP, baggage)

    kwargs['headers'][HTTP_TRACE_ID] = hex(int(baggage['trace_id']))[2:]  # strip '0x'
    kwargs['headers'][HTTP_SPAN_ID] = hex(int(baggage['span_id']))[2:]
    for key, value in baggage['baggage'].items():
        kwargs['headers']['{}{}'.format(HTTP_BAGGAGE_PREFIX, key)] = value

    return (method, url), kwargs
