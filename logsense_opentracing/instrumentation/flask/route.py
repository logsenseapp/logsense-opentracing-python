import opentracing
from ..utils import HTTP_TRACE_ID, HTTP_SPAN_ID, HTTP_BAGGAGE_PREFIX


def flask_route(scope, *args, **kwargs):  # pylint: disable=unused-argument
    """
    Extract information from flask request and put into opentracing scope

    ::

        import logging
        import asyncio
        from flask import Flask
        import opentracing

        from logsense_opentracing.tracer import Tracer
        from logsense_opentracing.instrumentation import patch_decorator, flask_route
        from logsense_opentracing.utils import setup_tracer


        app = Flask('hello-flask')

        # Initialize tracer
        setup_tracer(logsense_token='your own personal token')

        # Decorator should be patched before using it.
        patch_decorator('flask.Flask.route', before=flask_route, flat=False, alternative=True)

        # Define routing
        @app.route("/sayHello/<name>")
        def say_hello(name):
            import logging
            logging.info('User %s entered', name)
            return 'Hello {}'.format(name)


        # Run application
        if __name__ == "__main__":
            app.run(port=8080)
    """
    from flask import request  # Optional import

    # Extract trace if available
    carrier = {
        'baggage': {}
    }
    if request.headers.get(HTTP_TRACE_ID):
        try:
            carrier['trace_id'] = int(request.headers[HTTP_TRACE_ID], 16)
        except ValueError:
            log.warning('Incorrect header value: %s', request.headers[HTTP_TRACE_ID])

    if request.headers.get(HTTP_SPAN_ID):
        try:
            carrier['span_id'] = int(request.headers[HTTP_SPAN_ID], 16)
        except ValueError:
            log.warning('Incorrect header value: %s', request.headers[HTTP_SPAN_ID])

    prefix_len = len(HTTP_BAGGAGE_PREFIX)

    for name, value in request.headers.items():
        if name.startswith(HTTP_BAGGAGE_PREFIX) and name != HTTP_BAGGAGE_PREFIX:
            carrier[name[prefix_len:]] = value

    try:
        opentracing.tracer.extract(opentracing.propagation.Format.TEXT_MAP, carrier)
    except Exception as exception:
        log.warning(exception)

    # Extract request information
    scope.span.set_tag('http.url', request.url)
    scope.span.set_tag('http.method', request.method)
    scope.span.set_tag('peer.ipv4', request.remote_addr)

    return args, kwargs
