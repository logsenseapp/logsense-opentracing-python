"""
Example of instrumentation of asynchronous functions
"""
import logging
from time import sleep

import opentracing

from logsense_opentracing.utils import setup_tracer
from logsense_opentracing.instrumentation import patch_async_single, patch_module
from logsense_opentracing.tracer import _DummySender

# Initialize dummy tracer
setup_tracer(component='patch_module')


def finish():
    # Ensure all logs were sent correctly
    opentracing.tracer.finish()

class TestModule:
    @staticmethod
    def func_1():  # pylint: disable=missing-docstring
        logging.info('Inside function 1')
        sleep(3)
        TestModule.func_2()
        logging.info('Going out function 1')

    @staticmethod
    def func_2():  # pylint: disable=missing-docstring
        logging.info('Inside function 2')

    @staticmethod
    def main():  # pylint: disable=missing-docstring
        logging.info('Main function start')
        TestModule.func_1()
        TestModule.func_2()
        logging.info('Main function end')
        finish()


# Add instrumentation without doing enything in original functions
patch_module('__main__', include_paths=['__main__'])

TestModule.main()
