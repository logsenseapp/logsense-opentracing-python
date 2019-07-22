"""
Run `nc -lp 8888` in linux console to see which headers was send exactly
"""
import logging
import requests
import tornado.ioloop
import tornado.web
import opentracing

from logsense_opentracing.utils import setup_tracer
from logsense_opentracing.instrumentation import patch_single, tornado_route, requests_baggage, patch_module

# Initialize tracer
setup_tracer(component='Requests')
patch_single('requests.api.request', before=requests_baggage)

with opentracing.tracer.start_active_span('parent-span') as scope:
    scope.span.set_baggage_item('suitcase', 'My docs with important information')
    requests.get('http://localhost:8888/', headers={'my-header': 'I\'m using opentracing'})
