import opentracing
from logsense_opentracing.utils import setup_tracer
from logsense_opentracing.instrumentation import patch_module, ALL_ARGS
from tests.sender import MockSender
from tests import resources

from unittest import TestCase

import logging


class TestRegularClass(TestCase):
    def setUp(self):
        self.sender = MockSender()
        setup_tracer('test_token', sender=self.sender)

    def test_module(self):
        patch_module('tests.module.module_class.ModuleClass')

    def tearDown(self):
        opentracing.tracer.finish()
