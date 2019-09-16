import time
import os
import sys
import logging


class ModuleClass:
    def function(self, foo, bar):
        logging.info('Hello %s:%s', foo, bar)

    async def async_function(self, foo, bar):
        logging.info('Hello %s:%s', foo, bar)
