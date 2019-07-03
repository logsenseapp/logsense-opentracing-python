import opentracing
from logsense_opentracing.utils import setup_tracer
from logsense_opentracing.instrumentation import patch_single, ALL_ARGS
from tests.sender import MockSender
from tests import resources

from unittest import TestCase

import logging


class TestRegularClass(TestCase):
    def setUp(self):
        self.sender = MockSender()
        setup_tracer('test_token', sender=self.sender)
        self.backup_regular_method = resources.RegularClass.regular_method
        self.backup_static_method = resources.RegularClass.static_method
        self.backup_class_method = resources.RegularClass.class_method

    def test_regular_method(self):
        patch_single('tests.resources.RegularClass.regular_method', ALL_ARGS)

        obj = resources.RegularClass()
        obj.regular_method('a', 'b')
        self.sender.wait_on_data()

        data = [record.data for record in self.sender.get_data()]

        self.assertEqual(data[0]['ot.operation_name'], 'tests.resources.regular_method')
        self.assertEqual(data[0].get('ot.kwarg.foo'), 'a')
        self.assertEqual(data[0].get('ot.kwarg.bar'), 'b')
        self.assertEqual(data[0].get('ot.kwarg.self'), str(obj))

        self.assertEqual(data[1]['message'], 'Here is a and b')

    def test_static_method(self):
        patch_single('tests.resources.RegularClass.static_method', ALL_ARGS)

        obj = resources.RegularClass()
        obj.static_method('a', 'b')
        self.sender.wait_on_data()

        data = [record.data for record in self.sender.get_data()]

        self.assertEqual(data[0]['ot.operation_name'], 'tests.resources.static_method')
        self.assertEqual(data[0].get('ot.kwarg.foo'), 'a')
        self.assertEqual(data[0].get('ot.kwarg.bar'), 'b')
        self.assertIsNone(data[0].get('ot.kwarg.self'))

        self.assertEqual(data[1]['message'], 'Here is a and b')

    def test_class_method(self):
        patch_single('tests.resources.RegularClass.class_method', ALL_ARGS)

        obj = resources.RegularClass()
        obj.class_method('a', 'b')
        self.sender.wait_on_data()

        data = [record.data for record in self.sender.get_data()]

        self.assertEqual(data[0]['ot.operation_name'], 'tests.resources.class_method')
        self.assertEqual(data[0].get('ot.kwarg.foo'), 'a')
        self.assertEqual(data[0].get('ot.kwarg.bar'), 'b')
        self.assertEqual(data[0].get('ot.kwarg.cls'), str(obj))

        self.assertEqual(data[1]['message'], 'Here is a and b for RegularClass')

    def tearDown(self):
        opentracing.tracer.finish()
        resources.RegularClass.regular_method = self.backup_regular_method
        resources.RegularClass.static_method = self.backup_static_method
        resources.RegularClass.class_method = self.backup_class_method
