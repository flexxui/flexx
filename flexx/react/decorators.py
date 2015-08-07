"""
The decorator functions that make up the core API for flexx.react.
"""

import sys

from .signals import Signal, SourceSignal, InputSignal, LazySignal, PropSignal


def _first_arg_is_func(ii):
    return len(ii) == 1 and (not isinstance(ii[0], Signal)) and callable(ii[0])


def connect(*input_signals):
    """ Decorator to transform a function into Signal object.
    
    A signal takes one or more signals as input (specified as arguments
    to this decorator) and may produce a new signal value. The function
    being wrapped should have an argument for each upstream signal, and
    its return value is used as the output signal value, unless that value
    is ``react.undefined`` (or just ``undefined`` in JS).
    
    When any of the input signals change, this signal is updated
    immediately (i.e. the wrapped function is called). 
    
    Example:
        
        .. code-block:: py
            
            @react.connect('first_name', 'last_name')
            def full_name(first, last):
                return first + ' ' + last
            
            @react.connect('full_name')
            def greet(n):
                print('Hello %s!' % n)
    """
    if (not input_signals) or _first_arg_is_func(input_signals):
        raise ValueError('Act signal must have upstream signals.')
    
    def _connect(func):
        frame = sys._getframe(1)
        s = Signal(func, input_signals, frame=frame)
        return s
    return _connect


def source(*input_signals):
    """ Decorator to transform a function into a SourceSignal object.
    
    Source signals produce signal values. The developer can set the
    value using the ``_set()`` method. The function being wrapped should
    have a single argument. If that argument has a default value, that
    value will be the signal's initial value. The wrapper function is
    intended to do validation on the value.
    
    Though not common, a source signal may have upstream signals like
    the input signal does.
    
    Example:
        
        .. code-block:: py
        
            @react.source
            def last_name(val):
                return str(val)
            
            # Developer sets value. Users should not use _set()!
            s1._set('Doe')
    """
    frame = sys._getframe(1)
    def _source(func):
        return SourceSignal(func, input_signals, frame=frame)
    
    if _first_arg_is_func(input_signals):
        func, input_signals = input_signals[0], []
        return _source(func)
    else:  # pragma: no cover
        return _source


def input(*input_signals):
    """ Decorator to transform a function into a InputSignal object.
    
    An input signal allows the user to set the value by calling the
    signal with the value as the argument. The function being wrapped
    should have a single argument. If that argument has a default value,
    that value will be the signal's initial value. The wrapper function
    is intended to do validation and cleaning/standardization on the
    user-specified value.
    
    Example:
        
        .. code-block:: py
        
            @react.input
            def first_name(val):
                return str(val)
            
            s1('John')  # Set the value
    
    Though not common, an input signal may have upstream signals. In
    that case, the wrapper function should have additional arguments
    for the signals. The function is called with no arguments to
    initialize the value, with one argument if the user sets the value,
    and with n+1 arguments when any of the (n) signals change.
    
    Example:
        
        .. code-block:: py
        
            @react.input('fahrenheit')
            def celcius(v=32, f=None):
                if f is None:
                    return float(v)
                else:
                    return (f - 32) / 1.8
    """
    frame = sys._getframe(1)
    def _input(func):
        return InputSignal(func, input_signals, frame=frame)
    
    if _first_arg_is_func(input_signals):
        func, input_signals = input_signals[0], []
        return _input(func)
    else:
        return _input


def prop(*input_signals):
    """ Decorator to transform a function into a PropSignal object.
    
    A prop signal is a special kind of input signal that allows the
    user to set and get the value by assignment.
   
    This works, but not sure if this is a good idea API-wise, because
    it is not consistent with how signals work, and it hides the signal
    object. However, it could provide a way to bring FRP to systems
    that make heavy use of properties.
    """
    frame = sys._getframe(1)
    def _prop(func):
        return PropSignal(func, input_signals, frame=frame)
    
    if _first_arg_is_func(input_signals):
        func, input_signals = input_signals[0], []
        return _prop(func)
    else:  # pragma: no cover
        return _prop


def lazy(*input_signals):
    """ Decorator to transform a function into a LazySignal object.
    
    A lazy signal does *not* immediately update when any of its upstream
    signals changes. Instead, the signal is marked "invalid", but it
    will not retrieve the new signal value until it is requested. This
    pull machanism allows lazy evaluation and can prevent unnesesary
    updates.
    
    Example:
        
        .. code-block:: py
        
            @react.lazy('s1', 's2')
            def the_sum(val1, val2):
                return val1 + val2
    """
    if (not input_signals) or _first_arg_is_func(input_signals):
        raise ValueError('Lazy signal must have upstream signals.')
    
    def _lazy(func):
        frame = sys._getframe(1)
        s = LazySignal(func, input_signals, frame=frame)
        return s
    return _lazy    
