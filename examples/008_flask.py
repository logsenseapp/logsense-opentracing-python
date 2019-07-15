import logging
import asyncio
from flask import Flask
import opentracing

from logsense_opentracing.tracer import Tracer
from logsense_opentracing.instrumentation import patch_decorator, flask_route
from logsense_opentracing.utils import setup_tracer


app = Flask('hello-flask')

# Initialize tracer
setup_tracer(component='flask')

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
