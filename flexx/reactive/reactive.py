"""
Signals and reactions, the Functional Reactive Programming approach to events.

THINGS I FEEL UNCONFORTABLE ABOUT

* signal name is derived from func, which might be a lambda or buildin.
* "input signals" as a term for upstream signals
* binding for connecting (vs Python bound methods)

QUESTIONS / TODO

* serializing signal values to json, maybe support base types and others need
  a __json__ function.
* Predefined inputs? Str, Int, etc?
* Dynamism
* Binding is now simple and predictable, should we be smarter?
  For instance by binding unbound signals in the same frame when calling?

"""

import sys
import time
import inspect
import weakref
import logging


if sys.version_info >= (3, ):
    string_types = str
else:
    string_types = basestring


class UnboundError(Exception):
    def __init__(self, msg='This signal is not bound.'):
        Exception.__init__(self, msg)


# todo: we need access to the locals in which the object was instantiated too
class FakeFrame(object):
    """ Simulate an class instance (usually from HasSignals) as a frame,
    or to have a dummy (empty) frame for pure inputs.
    """
    def __init__(self, ob, globals):
        if ob is not None:
            self._ob = weakref.ref(ob)
        else:
            self._ob  = lambda x=None:None
        self._globals = globals
    
    @property
    def f_locals(self):
        ob = self._ob() 
        if ob is not None:
            locals = ob.__dict__.copy()
            # Handle signals. Not using __signals__; works on any class
            for key, val in ob.__class__.__dict__.items():
                if isinstance(val, Signal):
                    private_name = '_' + key
                    if private_name in locals:
                        locals[key] = locals[private_name]
            return locals
        return {}
    
    @property
    def f_globals(self):
        return self._globals


class Signal(object):
    """ A Signal is an object that provides a value that changes in time.
    
    The current value can be obtained by calling the signal object.
    
    Parameters:
    func: the function that determines how the output value is generated
          from the input signals.
    upstream: a list of signals that this signal depends on.
    """
    
    def __init__(self, func, upstream, frame=None, ob=None):
        # Check and set func
        assert callable(func)
        self._func = func
        self._name = func.__name__
        
        # Check and set dependencies
        upstream = [s for s in upstream]
        for s in upstream:
            assert isinstance(s, string_types)  # or isinstance(s, Signal)
        self._upstream_given = [s for s in upstream]
        self._upstream = []
        self._downstream = []
        
        # Frame and object
        self._frame = frame or sys._getframe(1)
        self._ob = weakref.ref(ob) if (ob is not None) else None
        
        # Get whether function is bound
        try:
            self._func_is_bound = inspect.getargspec(func)[0][0] in ('self', 'this')
        except (TypeError, IndexError):
            self._func_is_bound = False
        
        # Check whether this signals is (supposed to be) on a class, or not
        self._class_desciptor = None
        if (ob is None) and self._func_is_bound:
            self._class_desciptor = True
        if (ob is not None) and not self._func_is_bound:
            raise RuntimeError('Bound signals must have self/this argument.')
        
        # Init variables related to the signal value
        self._value = None
        self._last_value = None
        self._timestamp = 0
        self._last_timestamp = 0
        self._dirty = True
        
        # Binding
        self._unbound = 'No binding attempted yet.'
        self.bind(False)

    def __repr__(self):
        des = '-descriptor' if self._class_desciptor else ''
        bound = '(unbound)' if self.unbound else 'with value %r' % self._value
        return '<%s%s %r %s at 0x%x>' % (self.__class__.__name__, des, self._name, 
                                       bound, id(self))
    
    @property
    def __self__(self):
        """ The HasSignals instance that this signal is associated with
        (stored as a weak reference internally). None for plain signals.
        """
        if self._ob is not None:
            return self._ob()
    
    @property
    def name(self):
        """ The name of this signal, as inferred from the function that
        this signal wraps.
        """
        return self._name
    
    ## Behavior for when attached to a class
    
    def __set__(self, obj, value):
        raise ValueError('Cannot overwrite a signal; use some_signal(val) on InputSignal objects.')
    
    def __delete__(self, obj):
        raise ValueError('Cannot delete a signal.')
    
    def __get__(self, instance, owner):
        if not self._class_desciptor:
            self._class_desciptor = True
            self.bind(False)  # trigger unsubscribe
        if instance is None:
            return self
        
        private_name = '_' + self._name
        try:
            return getattr(instance, private_name)
        except AttributeError:
            frame = FakeFrame(instance, self._frame.f_globals)
            new = self.__class__(self._func, self._upstream_given, frame, ob=instance)
            setattr(instance, private_name, new)
            return new
    
    ## Binding
    
    def bind(self, raise_on_fail=True):
        """ Bind input signals
        
        Signals that are provided as a string are resolved to get the
        signal object, and this signal subscribes to the upstream
        signals.
        
        If resolving the signals from the strings fails, raises an
        error. Unless ``raise_on_fail`` is False, in which case we return
        True on success.
        """
        
        # Disable binding for signal placeholders on classes
        if self._class_desciptor:
            self.unbind()
            self._unbound = 'Cannot bind signal descriptors on a class.'
            if raise_on_fail:
                raise RuntimeError(self._unbound)
            return False
        
        # Resolve signals
        self._unbound = self._resolve_signals()
        if self._unbound:
            if raise_on_fail:
                raise RuntimeError('Bind error in signal %r: ' % self._name + self._unbound)
            return False
        
        # Subscribe
        for signal in self._upstream:
            signal._subscribe(self)
        
        # If binding complete, update (or not)
        self._set_dirty(self)
    
    def unbind(self):
        """ Unbind this signal, unsubscribing it from the upstream signals.
        """
        while self._upstream:
            s = self._upstream.pop(0)
            s._unsubscribe(self)
        self._unbound = 'Explicitly unbound via unbind()'
    
    def _resolve_signals(self):
        """ Get signals from their string path. Return value to store
        in _unbound (False means success). Should only be called from
        bind().
        """
        
        upstream = []
        
        for fullname in self._upstream_given:
            nameparts = fullname.split('.')
            # Obtain first part of path from the frame that we have
            n = nameparts[0]
            ob = self._frame.f_locals.get(n, self._frame.f_globals.get(n, None))
            # Walk down the object tree to obtain the full path
            for name in nameparts[1:]:
                if isinstance(ob, Signal):
                    ob = ob()
                ob = getattr(ob, name, None)
                if ob is None:
                    return 'Signal %r does not exist.' % fullname
            # Add to list or fail
            if not isinstance(ob, Signal):
                return 'Object %r is not a signal.' % fullname
            upstream.append(ob)
        
        self._upstream[:] = upstream
        return False  # no error
    
    def _subscribe(self, signal):
        """ For a signal to subscribe to this signal.
        """
        if signal not in self._downstream:
            self._downstream.append(signal)
    
    def _unsubscribe(self, signal):
        """ For a signal to unsubscribe from this signal.
        """
        while signal in self._downstream:
            self._downstream.remove(signal)
    
    @property
    def unbound(self):
        """ False when bound. Otherwise this is a string with a message
        why the signal is not bound.
        """
        return self._unbound
    
    ## Getting and setting signal value
    
    def _save_update(self):
        """ Update our signal, when an error occurs, we print it and set
        sys.last_X for PM debugging, but return as usual.
        """
        try:
            self()
        except Exception:
            # Allow post-mortem debugging
            type_, value, tb = sys.exc_info()
            tb = tb.tb_next  # Skip *this* frame
            sys.last_type = type_
            sys.last_value = value
            sys.last_traceback = tb
            del tb  # Get rid of it in this namespace
            logging.exception(value)
    
    @property
    def value(self):
        """ The current signal value.
        """
        return self()
    
    @property
    def last_value(self):
        """ The previous signal value. Getting this value will *not*
        update the signal; the returned value corresponds to the value
        right before the last time that the signal was updated.
        """
        return self._last_value
    
    def _set_value(self, value):
        """ This is like ``self._value = value``, but with bookkeeping.
        """
        self._last_value = self._value
        self._value = value
        self._last_timestamp = self._timestamp
        self._timestamp = time.time()
        self._dirty = False
    
    def _get_value(self):
        """ Get the current value. Some overhead is put here to keep
        update_value compact.
        """
        if self._unbound:
            self.bind(False)
        if self._unbound:
            raise UnboundError()
        if self._dirty == True:
            self._update_value()
        return self._value
    
    def _update_value(self):
        """ Get the latest value from upstream. This method can be overloaded.
        """
        try:
            args2 = [s() for s in self._upstream]
        except UnboundError:
            return
        value = self._call(*args2)
        self._set_value(value)
    
    def __call__(self, *args):
        """ Get the signal value.
        
        If the signals is unbound, raises UnBoundError. If an upstream
        signal is unbound, errr, what should we do?
        """
        # todo: what to do when an upstream signal (or upstream-upstream) is unbound?
        
        if not args:
            return self._get_value()
        else:
            raise RuntimeError('Can only set signal values of InputSignal objects.')
    
    def _call(self, *args):
        if self._ob is not None:
            return self._func(self._ob(), *args)
        else:
            return self._func(*args)
    
    def _set_dirty(self, initiator):
        """ Called by upstream signals when their value changes.
        """
        if self._dirty or self is initiator:
            return
        # Update self
        self._dirty = True
        # Allow downstream to update
        for signal in self._downstream:
            signal._set_dirty(initiator)
        # Note: we do not update our value now; lazy evaluation. See
        # the ReactSignal for pushing changes downstream immediately.


class SourceSignal(Signal):
    """ A signal that has no upstream signals, but produces values by itself.
    
    From the programmer's perspective, this is similar to an
    InputSignal, where the programmer sets the value with the ``_set()``
    method. Users of the signal should typically *not* use this private
    method.
    
    """
    
    def _update_value(self):
        
        # Try to initialize, func might not have a default value
        if self._timestamp == 0:
            try:
                value = self._call()
            except Exception:
                self._dirty = False
            else:
                self._set_value(value)
                return  # do not get from upstream initially
        
        # Get value from upstream
        if self._upstream:
            try:
                args2 = [self._value] + [s() for s in self._upstream]
            except UnboundError:
                return
            value = self._call(*args2)
            self._set_value(value)
    
    def _set(self, value):
        """ Method for the developer to set the source signal.
        """
        self._set_value(self._call(value))
        for signal in self._downstream:
            signal._set_dirty(self)
    
    def _set_dirty(self, initiator):
        # An input signal that has upstream signals is reactive too.
        Signal._set_dirty(self, initiator)
        self._save_update()


class InputSignal(SourceSignal):
    """ InputSignal objects are special signals for which the value can
    be set by the user, by calling the signal with a single argument.
    
    The function associated with the signal is used to validate the
    use-specified value.
    
    """
    
    def __call__(self, *args):
        """ Get the signal value.
        
        If the signals is unbound, raises UnBoundError. If an upstream
        signal is unbound, errr, what should we do?
        """
        # todo: what to do when an upstream signal (or upstream-upstream) is unbound?
        
        if not args:
            return self._get_value()
        elif len(args) == 1:
            return self._set(args[0])
        else:
            raise ValueError('Setting an input signal requires exactly one argument')


class ReactSignal(Signal):
    """ A signal that reacts immediately to changes of upstream signals.
    """ 
    def _set_dirty(self, initiator):
        Signal._set_dirty(self, initiator)
        self._save_update()


class HasSignals(object):
    """ A base class for objects with signals.
    
    Creating signals on this class will provide each instance of this
    class to have corresponding signals. During initialization the
    signals are bound, and this class has a ``bind_unbound()`` method
    to easily allow binding any unbound signals at a latere time.
    
    Note that signals can be attached to any class, but then each signal
    will have to be "touched" to create the signal instance, and the
    signals might not be initially bound.
    
    Functions defined on this class that are wrapped by signals should
    have a ``self`` argument (``this`` is also allowed).
    """
    
    def __init__(self):
        
        # Instantiate signals, its enough to reference them
        self.__signals__ = []
        for key, val in sorted(self.__class__.__dict__.items()):
            if isinstance(val, Signal):
                getattr(self, key)
                self.__signals__.append(key)
        
        self.bind_unbound(True)
    
    def bind_unbound(self, raise_on_fail=True):
        """ Bind any unbound signals associated with this object.
        """
        success = True
        for name in self.__signals__:
            s = getattr(self, name)
            if s.unbound:
                print('unbound', s)
                bound = s.bind(raise_on_fail)  # dont combine this with next line
                success = success and bound
        return success


def _first_arg_is_func(ii):
    return len(ii) == 1 and (not isinstance(ii[0], Signal)) and callable(ii[0])


def source(*input_signals):
    """ Decorator to transform a function into a SourceSignal object.
    
    Source signals produce signal values. The developer can set the
    value using the ``_set()`` method. The wrapper function is intended
    can be used to modify the input, in the same way as for the input
    signal.
    
    Example:
    
        @source
        def s1(val):
            return float(val)
        
        # Developer sets value. Users should not use _set()!
        s1._set(42)
    
    Similar to the InputSignal, the SourceSignal may have upstream signals.
    
    """
    def _source(func):
        frame = FakeFrame(None, {})
        s = SourceSignal(func, [], frame=frame)
        return s
    def _source_with_signals(func):
        frame = sys._getframe(1)
        s = InputSignal(func, input_signals, frame=frame)
        return s
    
    if _first_arg_is_func(input_signals):
        return _source(input_signals[0])
    else:
        return _source_with_signals


def input(*input_signals):
    """ Decorator to transform a function into a InputSignal object.
    
    An input signal commonly has 0 input signals, but allows the user
    to set the output value, by calling the signal with the value as the
    argument. The function being wrapped should have a single argument.
    If that argument has a default value, that value will be the
    signal's initial value. The wrapper function is intended to do
    validation and cleaning/standardization on the user-specified input.
    
    Example:
    
        @input
        def s1(val):
            return float(val)
        
        s1(42)  # Set the value
    
    Though not common, an input signal may actually also have upstream
    signals. In that case, the wrapper function should have additional
    arguments for the signals. The function is called with no arguments to
    initialize the value, with one argument if the user sets the value, and
    with n+1 arguments when any of the (n) signals change.
    
    Example:
    
        @input('fahrenheit')
        def celcius(v=32, f=None):
            if f is None:
                return float(v)
            else:
                return (f - 32) / 1.8
    
    """
    def _input(func):
        frame = FakeFrame(None, {})
        s = InputSignal(func, [], frame=frame)
        return s
    def _input_with_signals(func):
        frame = sys._getframe(1)
        s = InputSignal(func, input_signals, frame=frame)
        return s
    
    if _first_arg_is_func(input_signals):
        return _input(input_signals[0])
    else:
        return _input_with_signals


def signal(*input_signals):  # todo: rename?
    """ Decorator to transform a function into a Signal object.
    
    A signal takes one or more signals as input (specified as arguments
    to this decorator) and produces a new signal value. The function
    being wrapped should have an argument for each upstream signal, and
    its return value is used as the output signal value.
    
    Example:
    
        @signal('s1', 's2')
        def adder(val1, val2):
            return val1 + val2
    
    When any of the input signals change, this signal is marked "invalid",
    but it will not retrieve the new signal value until it is requested.
    This pull machanism differs from the ``react`` decorator.
    """
    if (not input_signals) or _first_arg_is_func(input_signals):
        raise ValueError('Input signal must have upstream signals.')
    
    def _signal(func):
        frame = sys._getframe(1)
        s = Signal(func, input_signals, frame=frame)
        return s
    return _signal    


def react(*input_signals):
    """ Decorator to transform a function into a ReactSignal object.
    
    A react signal takes one or more signals as input (specified as
    arguments to this decorator) and may produce a new signal value.
    The function being wrapped should have an argument for each upstream
    signal, and its return value is used as the output signal value.
    The ReactSignal is commonly used for end-signals, which require no
    output signal.
    
    Example:
    
        @react('s1', 's2')
        def show_values(val1, val2):
            print(val1, val2)
    
    When any of the input signals change, this signal is updated
    immediately (i.e. the wrapped function is called). This push
    machanism differs from the ``signal`` decorator.
    """
    if (not input_signals) or _first_arg_is_func(input_signals):
        raise ValueError('Input signal must have upstream signals.')
    
    def _react(func):
        frame = sys._getframe(1)
        s = ReactSignal(func, input_signals, frame=frame)
        return s
    return _react
