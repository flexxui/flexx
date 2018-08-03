"""
Improved logging facilities:

* info and debug messages are printed to stdout instead of stderr.
* if level is set to debug, will show source of each message.
* ability to filter messages with a regexp.
* provides a context manager to capture log messages in a list.

This code can be put anywhere in your project, then import
set_log_level()
"""

# The code in this file is inspired by similar code from the Vispy project

import re
import sys
import time
import logging
import traceback


MODULE_NAME = __name__.split('.')[0]

logging_types = dict(debug=logging.DEBUG, info=logging.INFO,
                     warning=logging.WARNING, error=logging.ERROR,
                     critical=logging.CRITICAL)


class _Formatter(logging.Formatter):
    """Formatter that optionally prepends caller """

    def __init__(self):
        super().__init__()  # '%(levelname)s %(name)s: %(message)s')
        self.prepend_caller = False

    def format(self, record):
        base = '[{} {} {}] '.format(record.levelname[0],
                                    time.strftime('%H:%M:%S'),
                                    record.name)
        if isinstance(record.msg, Exception):
            # Get excepion info and skip first frames
            type_, value, tb = sys.exc_info()
            for _ in range(getattr(value, 'skip_tb', 0)):
                tb = tb.tb_next
            # Enable post mortem debugging
            sys.last_type = type_
            sys.last_value = value
            sys.last_traceback = tb
            # Compose message
            cname = type_.__name__
            out = ''.join(traceback.format_list(traceback.extract_tb(tb)))
            del tb  # we don't want to hold too much references to this
            return base + cname + ': ' + str(value) + '\n' + out.rstrip()
        else:
            out = base + str(record.msg % record.args)
            if self.prepend_caller:
                part1, part2 = out.split(':', 1)
                out = part1 + ' ' + record.funcName + '():' + part2
            return out


class _Handler(logging.StreamHandler):
    """ Stream handler that prints INFO and lower to stdout
    """

    def emit(self, record):
        if record.levelno >= logging.WARNING:
            self.stream = sys.stderr
        else:
            self.stream = sys.stdout
        super().emit(record)


class _MatchFilter:
    """ To filter records on regexp matches.
    """
    def __init__(self):
        self.match = None

    def filter(self, record):
        match = self.match
        if not match:
            return True
        elif isinstance(match, str):
            return (match in record.name or
                    match in record.getMessage() or
                    match in record.funcName)
        else:
            return (re.search(match, record.name) or
                    re.search(match, record.getMessage()) or
                    re.search(match, record.funcName))


class _CaptureFilter:
    """ To collect records in the capture_log context.
    """
    def __init__(self):
        self.records = []

    def filter(self, record):
        self.records.append(_formatter.format(record))
        return False


def set_log_level(level, match=None):
    """Set the logging level and match filter

    Parameters:
        level (str, int): The verbosity of messages to print.
            If a str, it can be either DEBUG, INFO, WARNING, ERROR, or
            CRITICAL. Note that these are for convenience and are equivalent
            to passing in logging.DEBUG, etc.
        match (str, regexp, None): String to match. Only those messages
            that contain ``match`` as a substring (and has the
            appropriate ``level``) will be displayed. Match can also be
            a compiled regexp.

    Notes
    -----
    If level is DEBUG, the method emitting the log message will be
    prepended to each log message. Note that if ``level`` is DEBUG or
    if the ``match`` option is used, a small overhead is added to each
    logged message.
    """
    if isinstance(level, str):
        level = level.lower()
        if level not in logging_types:
            raise ValueError('Invalid argument "%s"' % level)
        level = logging_types[level]
    elif not isinstance(level, int):
        raise TypeError('log level must be an int or string')
    logger.setLevel(level)
    _filter.match = match
    _formatter.prepend_caller = level <= logging.DEBUG


class capture_log:
    """ Context manager to capture log messages. Useful for testing.
    Usage:

    .. code-block:: python

        with capture_log(level, match) as log:
            ...
        # log is a list strings (as they would have appeared in the console)
    """

    def __init__(self, level, match=None):
        self._args = level, match

    def __enter__(self):
        self._old_args = logger.level, _filter.match
        set_log_level(*self._args)
        self._filter = _CaptureFilter()
        _handler.addFilter(self._filter)
        return self._filter.records

    def __exit__(self, type, value, traceback):
        _handler.removeFilter(self._filter)
        set_log_level(*self._old_args)


# Create logger

logger = logging.getLogger(MODULE_NAME)
logger.propagate = False
logger.setLevel(logging.INFO)

# Remove previous handlers, these can be leftovers when flexx is re-imorted,
# as can happen during tests
h = None
for h in list(logger.handlers):
    if h.__class__.__module__ == __name__:
        logger.removeHandler(h)
del h

_handler = _Handler()
_filter = _MatchFilter()
_formatter = _Formatter()

logger.addHandler(_handler)
_handler.addFilter(_filter)
_handler.setFormatter(_formatter)
