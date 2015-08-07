"""
The decorator functions that make up the core API for flexx.react.
"""

import sys

from .signals import Signal, SourceSignal, InputSignal, WatchSignal, ActSignal, PropSignal


def _first_arg_is_func(ii):
    return len(ii) == 1 and (not isinstance(ii[0], Signal)) and callable(ii[0])


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
        
            @source
            def s1(val):
                return float(val)
            
            # Developer sets value. Users should not use _set()!
            s1._set(42)
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
        
            @input
            def s1(val):
                return float(val)
            
            s1(42)  # Set the value
    
    Though not common, an input signal may have upstream signals. In
    that case, the wrapper function should have additional arguments
    for the signals. The function is called with no arguments to
    initialize the value, with one argument if the user sets the value,
    and with n+1 arguments when any of the (n) signals change.
    
    Example:
        
        .. code-block:: py
        
            @input('fahrenheit')
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


def watch(*input_signals):
    """ Decorator to transform a function into a WatchSignal object.
    
    A watch signal takes one or more signals as input (specified as arguments
    to this decorator) and produces a new signal value. The function
    being wrapped should have an argument for each upstream signal, and
    its return value is used as the output signal value.
    
    When any of the input signals change, this signal is marked
    "invalid", but it will not retrieve the new signal value until it
    is requested. This pull machanism allows lazy evaluation and can
    prevent unnesesary updates.
    
    Example:
        
        .. code-block:: py
        
            @watch('s1', 's2')
            def the_sum(val1, val2):
                return val1 + val2
    """
    if (not input_signals) or _first_arg_is_func(input_signals):
        raise ValueError('Input signal must have upstream signals.')
    
    def _signal(func):
        frame = sys._getframe(1)
        s = WatchSignal(func, input_signals, frame=frame)
        return s
    return _signal    


def act(*input_signals):
    """ Decorator to transform a function into ActSignal object.
    
    An act signal takes one or more signals as input (specified as
    arguments to this decorator) and may produce a new signal value.
    The function being wrapped should have an argument for each upstream
    signal, and its return value (if any) is used as the output signal
    value.
    
    When any of the input signals change, this signal is updated
    immediately (i.e. the wrapped function is called). This push
    machanism differs from the ``watch`` decorator.
    
    The act signal is commonly used for end-signals to react to certain
    changes in the application.
    
    Example:
        
        .. code-block:: py
        
            @act('s1', 's2')
            def show_values(val1, val2):
                print(val1, val2)
    """
    if (not input_signals) or _first_arg_is_func(input_signals):
        raise ValueError('Act signal must have upstream signals.')
    
    def _react(func):
        frame = sys._getframe(1)
        s = ActSignal(func, input_signals, frame=frame)
        return s
    return _react
