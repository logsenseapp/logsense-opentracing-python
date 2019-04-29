"""
Logging handler for logsense opentracing.
It is quite different from used in logsense-logger,
because responsibility for sending data to the collector is moved to the tracer
"""
import logging
import opentracing

class OpentracingLogsenseHandler(logging.Handler):
    """
    Logging Handler for logsense  opentracing.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def emit(self, record):
        active_span = opentracing.tracer.active_span
        if active_span is None:
            return None

        dict_to_log = {
            'logger.name': record.name,
            'logger.level': record.levelname,
            'logger.pathname': record.pathname,
            'logger.lineno': record.lineno,
            'logger.exc_info': record.exc_info,
            'logger.func': record.funcName
        }

        if isinstance(record.msg, dict):
            dict_to_log.update(record.msg)
        else:
            dict_to_log['message'] = record.getMessage()

        print(dict_to_log)
        active_span.log_kv(dict_to_log)
        return None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
