"""
This application base on https://github.com/PacktPublishing/Mastering-Distributed-Tracing

"""
import logging
import asyncio
import random
from time import sleep
from flask import Flask
import opentracing

from logsense_opentracing.tracer import Tracer
from logsense_opentracing.instrumentation import patch_decorator, patch_single, flask_route


app = Flask('hello-flask')  # pylint: disable=invalid-name

log = logging.getLogger()  # pylint: disable=invalid-name
tracer = Tracer()  # pylint: disable=invalid-name
opentracing.tracer = tracer
ioloop = asyncio.get_event_loop()  # pylint: disable=invalid-name

patch_decorator('flask.Flask.route', before=flask_route)

@app.route("/sayHello/<name>")
def say_hello(name):  # pylint: disable=missing-docstring
    person = get_person(name)
    resp = TestClass.format_greeting(
        name=person['name'],
        title=person['title'],
        description=person['description']
    )
    return resp


def get_person(name):  # pylint: disable=missing-docstring
    person = {
        'name': name,
        'title': name,
        'description': name
    }

    return person

class TestClass:  # pylint: disable=missing-docstring,too-few-public-methods
    @staticmethod
    def format_greeting(name,
                        title,
                        description,
                        new_argument='test_argument'):  # pylint: disable=missing-docstring,unused-argument
        if name == 'Sleep':
            sleep(10)
        else:
            sleep(random.randint(0, 4))

        greeting = 'Hello, '
        if title:
            greeting += title + ' '
        greeting += name + '!'
        if description:
            greeting += ' ' + description
        return greeting


if __name__ == "__main__":
    patch_single('__main__.get_person')
    patch_single('__main__.TestClass.format_greeting')
    app.run(port=8080)
