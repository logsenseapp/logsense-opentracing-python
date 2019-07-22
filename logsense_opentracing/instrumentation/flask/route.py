"""
`Flask <https://palletsprojects.com/p/flask/>`_ integration
"""
from ..utils import extract_http_carrier


def flask_route(scope, *args, **kwargs):  # pylint: disable=unused-argument
    """
    Extract information from flask request and put into opentracing scope

    ::

        import logging
        from flask import Flask

        from logsense_opentracing.instrumentation import patch_decorator, flask_route
        from logsense_opentracing.utils import setup_tracer


        app = Flask('hello-flask')

        # Initialize tracer
        setup_tracer(component='flask')

        # Decorator should be patched before using it.
        patch_decorator('flask.Flask.route', before=flask_route, flat=False, only_decorated=True)

        # Define routing
        @app.route("/sayHello/<name>")
        def say_hello(name):
            \"\"\"
            Log client's name which entered our application and send message to it
            \"\"\"
            logging.info('User %s entered', name)
            return 'Hello {}'.format(name)


        # Run application
        if __name__ == "__main__":
            app.run(port=8080)

    :param scope: Opentracing's scope
    :type scope: ``opentracing.Scope``
    """
    from flask import request  # Optional import, not everyone is going to install flask module

    extract_http_carrier(request.headers)

    # Extract request information
    scope.span.set_tag('http.url', request.url)
    scope.span.set_tag('http.method', request.method)
    scope.span.set_tag('peer.ipv4', request.remote_addr)

    return args, kwargs
