"""
Functions to allow *Functional* Reactive Programming. Each of these
functions produces a new signal.
"""

import sys

from .signals import Signal
from .signals import undefined


def merge(*signals):
    """ Merge all signal values into a tuple.
    """
    frame = sys._getframe(1)
    def _merge(*values):
        return values
    return Signal(_merge, signals, frame)


def filter(func, signal):
    """ Filter the values of a signal.
    
    The given function receives the signal value as an argument. If the
    function returns Truthy, the value is passed, otherwise not.
    """
    frame = sys._getframe(1)
    def _filter(value):
        if func(value):
            return value
        return undefined
    return Signal(_filter, [signal], frame)


def map(func, signal):
    """ Map a function to the value of a signal.
    """
    frame = sys._getframe(1)
    def _map(value):
        return func(value)
    return Signal(_map, [signal], frame)


def reduce(func, signal, initval=None):
    """ Accumulate values, similar to Python's reduce() function.
    """
    frame = sys._getframe(1)
    val = []
    if initval is not None:
        val.append(initval)
    def _accumulate(value):
        if not val:
            val.append(value)
        else:
            val[0] = func(value, val[0])
        return val[0]
    return Signal(_accumulate, [signal], frame)
