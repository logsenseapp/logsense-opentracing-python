"""
Tornado handler example
"""
import logging
import tornado.ioloop
import tornado.web

from logsense_opentracing.utils import setup_tracer
from logsense_opentracing.instrumentation import patch_single, tornado_route


# Initialize tracer
setup_tracer(component='tornado server')


class MainHandler(tornado.web.RequestHandler):  # pylint: disable=missing-docstring, abstract-method

    def get(self):
        """
        Just log and send welcome message
        """
        logging.info('Hello, world')
        self.write('Hello, world')


# Patch handler
patch_single('__main__.MainHandler.get', before=tornado_route)


if __name__ == "__main__":
    app = tornado.web.Application([  # pylint: disable=invalid-name
        (r"/", MainHandler),
    ])
    app.listen(8889)
    tornado.ioloop.IOLoop.current().start()
