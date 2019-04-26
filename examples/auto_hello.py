"""
This application base on https://github.com/PacktPublishing/Mastering-Distributed-Tracing

"""
import logging
import asyncio
import opentracing
import random
from flask import Flask, request
from time import sleep

from logsense_opentracing.tracer import Tracer
from logsense_opentracing.instrumentation import patch_decorator, patch_single, flask_route


app = Flask('hello-flask')  # pylint: disable=invalid-name

log = logging.getLogger()  # pylint: disable=invalid-name
tracer = Tracer()  # pylint: disable=invalid-name
opentracing.tracer = tracer
ioloop = asyncio.get_event_loop()  # pylint: disable=invalid-name
number = random.randint(0, 10000)

patch_decorator('flask.Flask.route', flask_route)

@app.route("/sayHello/<name>")
def say_hello(name):
    person = get_person(name)
    resp = test_module.format_greeting(
        name=person['name'],
        title=person['title'],
        description=person['description']
    )
    return resp


def get_person(name):
    person = {
        'name': name,
        'title': name,
        'description': name
    }

    return person

class test_module:
    @staticmethod
    def format_greeting(name, title, description, new_argument='test_argument'):
        if name == 'Sleep':
            sleep(10)
        else:
            sleep(random.randint(0,4))

        greeting = 'Hello, '
        if title:
            greeting += title + ' '
        greeting += name + '!'
        if description:
            greeting += ' ' + description
        return greeting


if __name__ == "__main__":
    patch_single('__main__.get_person')
    patch_single('__main__.test_module.format_greeting')
    app.run(port=8080)
