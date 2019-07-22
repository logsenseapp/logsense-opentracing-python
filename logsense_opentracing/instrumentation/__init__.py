"""
`Instrumentation` takes together everything needed to automatic and manual instrumentation of python application
"""
from .general import instrumentation, remove_instrumentation, async_instrumentation
from .utils import ALL_ARGS
from .modules import patch_module
from .functions import patch_single, patch_async_single
from .decorators import patch_decorator, patch_async_decorator

from .flask.route import flask_route
from .tornado.route import tornado_route
from .requests.baggage import requests_baggage
