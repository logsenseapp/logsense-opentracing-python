import logging


# Functions
def regular_function(foo, bar):
    logging.error('This is %s %s', foo, bar)


# Classes
class RegularClass:
    def regular_method(self, foo, bar):
        logging.info('Here is %s and %s', foo, bar)

    @classmethod
    def class_method(cls, foo, bar):
        logging.info('Here is %s and %s for %s', foo, bar, cls.__name__)

    @staticmethod
    def static_method(foo, bar):
        logging.info('Here is %s and %s', foo, bar)