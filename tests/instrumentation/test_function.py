import opentracing
from logsense_opentracing.utils import setup_tracer
from logsense_opentracing.instrumentation import patch_single, ALL_ARGS
from tests.sender import MockSender
from tests import resources

from unittest import TestCase

import logging


class TestFunctions(TestCase):
    def setUp(self):
        self.sender = MockSender()
        setup_tracer('test_token', sender=self.sender)
        self.backup_regular_function = resources.regular_function

    def test_function(self):
        regular_function = patch_single('tests.resources.regular_function')

        regular_function('a', 'b')
        self.sender.wait_on_data()

        data = [record.data for record in self.sender.get_data()]

        self.assertEqual(data[0]['ot.operation_name'], 'tests.resources.regular_function')
        self.assertEqual(data[0]['_type'], 'trace')
        self.assertIsNone(data[0].get('ot.kwarg.foo'))
        self.assertIsNone(data[0].get('ot.kwarg.bar'))

        self.assertEqual(data[1]['message'], 'This is a b')

    def test_function_argument(self):
        regular_function = patch_single('tests.resources.regular_function', arguments=['foo'])

        regular_function('a', 'b')
        self.sender.wait_on_data()

        data = [record.data for record in self.sender.get_data()]

        self.assertEqual(data[0].get('ot.kwarg.foo'), 'a')
        self.assertIsNone(data[0].get('ot.kwarg.bar'))
        self.assertEqual(data[1]['message'], 'This is a b')

    def test_function_all_arguments(self):
        regular_function = patch_single('tests.resources.regular_function', arguments=ALL_ARGS)

        regular_function('a', 'b')
        self.sender.wait_on_data()

        data = [record.data for record in self.sender.get_data()]

        self.assertEqual(data[0].get('ot.kwarg.foo'), 'a')
        self.assertEqual(data[0].get('ot.kwarg.bar'), 'b')
        self.assertEqual(data[1]['message'], 'This is a b')

    def tearDown(self):
        opentracing.tracer.finish()
        resources.regular_function = self.backup_regular_function
