import logging
import requests
import tornado.ioloop
import tornado.web

from logsense_opentracing.utils import setup_tracer
from logsense_opentracing.instrumentation import patch_single, tornado_route, requests_baggage, patch_module

# Initialize tracer
setup_tracer(component='Main server')


class MainHandler(tornado.web.RequestHandler):

    def get(self):
        logging.info('Inside main server')
        self.write("Hello, world")
        requests.get('http://localhost:8889/')


patch_single('__main__.MainHandler.get', before=tornado_route)
patch_single('requests.api.request', before=requests_baggage)
patch_module('requests.models.PreparedRequest', recursive=True)

def make_app():
    return tornado.web.Application([
        (r"/", MainHandler)
    ])

if __name__ == "__main__":
    app = make_app()

    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()