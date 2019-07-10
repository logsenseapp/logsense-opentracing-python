import tornado.ioloop
import tornado.web
import requests
import logging

import opentracing

from logsense_opentracing.utils import setup_tracer
from logsense_opentracing.instrumentation import patch_single, tornado_route


# Initialize tracer
setup_tracer(component='Second server')


class MainHandler(tornado.web.RequestHandler):

    def get(self):
        logging.info('Inside second server')
        self.write("Hello, world")


patch_single('__main__.MainHandler.get', before=tornado_route)

def make_app():
    return tornado.web.Application([
        (r"/", MainHandler),
    ])

if __name__ == "__main__":
    app = make_app()
    app.listen(8889)
    tornado.ioloop.IOLoop.current().start()
