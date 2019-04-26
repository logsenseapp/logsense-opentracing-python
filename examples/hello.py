"""
This application base on https://github.com/PacktPublishing/Mastering-Distributed-Tracing

"""
import logging
import asyncio
import opentracing
import random
from flask import Flask

from logsense_opentracing.tracer import Tracer
from logsense_opentracing.instrumentation import patch_decorator


app = Flask('hello-flask')  # pylint: disable=invalid-name

log = logging.getLogger()  # pylint: disable=invalid-name
tracer = Tracer()  # pylint: disable=invalid-name
opentracing.tracer = tracer
ioloop = asyncio.get_event_loop()  # pylint: disable=invalid-name
number = random.randint(0, 10000)

@app.route("/sayHello/<name>")
def say_hello(name):
    with opentracing.tracer.start_active_span('say-hello') as scope:
        person = get_person(name)
        resp = format_greeting(
            name=person['name'],
            title=person['title'],
            description=person['description']
        )
        scope.span.set_tag('response', resp)
        scope.span.set_tag('number', number)
        return resp


def get_person(name):
    with opentracing.tracer.start_active_span('get-person') as scope:
        person = {
            'name': name,
            'title': name,
            'description': name
        }

        scope.span.log_kv(person)
        scope.span.set_tag('number', number)
        return person


def format_greeting(name, title, description):
    with opentracing.tracer.start_active_span('format-greeting') as scope:
        greeting = 'Hello, '
        if title:
            greeting += title + ' '
        greeting += name + '!'
        if description:
            greeting += ' ' + description
        scope.span.set_tag('number', number)
        return greeting


if __name__ == "__main__":
    app.run(port=8080)
