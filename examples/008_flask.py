"""
Extract information from flask request and put into opentracing scope
"""
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
    """
    Log client's name which entered our application and send message to it
    """
    logging.info('User %s entered', name)
    return 'Hello {}'.format(name)


# Run application
if __name__ == "__main__":
    app.run(port=8080)
