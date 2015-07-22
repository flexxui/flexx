"""
Signals and reactions, the Functional Reactive Programming approach to events.

THINGS I FEEL UNCONFORTABLE ABOUT

* signal name is derived from func, which might be a lambda or buildin.
* "input signals" as a term for upstream signals

QUESTIONS / TODO

* serializing signal values to json, maybe support base types and others need
  a __json__ function.
* Predefined inputs? Str, Int, etc?
* Dynamism
* docs
* asynchronous vs atomic?


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


undefined = 'JS UNDEFINED'  # to help make some code PyScript compattible


# From six.py
def with_metaclass(meta, *bases):
    """Create a base class with a metaclass."""
    # This requires a bit of explanation: the basic idea is to make a dummy
    # metaclass for one level of class instantiation that replaces itself with
    # the actual metaclass.
    class metaclass(meta):
        def __new__(cls, name, this_bases, d):
            return meta(name, bases, d)
    return type.__new__(metaclass, 'temporary_class', (), {})


class SignalValueError(Exception):
    pass


class StubFrame(object):
    """ Empty frame for source/input signals without upstream.
    """
    @property
    def f_locals(self):
        return {}
    
    @property
    def f_globals(self):
        return {}
    
    @property
    def f_back(self):
        return self


class ObjectFrame(object):
    """ A proxy frame that gives access to the class instance (usually
    from HasSignals) as a frame, combined with the frame that the class
    was defined in.
    """
    
    # We need to store the frame. If we stored the f_locals dict, it
    # would not be up-to-date by the time we need it. I suspect that
    # getattr(frame, 'f_locals') updates the dict.
    
    def __init__(self, ob, frame):
        self._ob = weakref.ref(ob)
        self._frame = frame
    
    @property
    def f_locals(self):
        locals = self._frame.f_locals.copy()
        ob = self._ob()
        if ob is not None:
            locals.update(ob.__dict__)
            # Handle signals. Not using __signals__; works on any class
            for key in dir(ob.__class__):
                if key.startswith('__'):
                    continue
                val = getattr(ob.__class__, key)
                if isinstance(val, Signal):
                    private_name = '_' + key + '_signal'
                    if private_name in locals:
                        locals[key] = locals[private_name]
        return locals
    
    @property
    def f_globals(self):
        return self._frame.f_globals
    
    @property
    def f_back(self):
        return ObjectFrame(self._ob(), self._frame.f_back)


class Signal(object):
    """ A Signal is an object that provides a value that changes in time.
    
    The current value can be obtained by calling the signal object.
    
    Parameters:
    func: the function that determines how the output value is generated
          from the input signals.
    upstream: a list of signals that this signal depends on.
    """
    _active = False
    
    def __init__(self, func, upstream, frame=None, ob=None):
        # Check and set func
        assert callable(func)
        self._func = func
        self._name = func.__name__
        
        # Set docstring this appears correct in sphinx docs
        self.__doc__ = 'Signal -> ' + (func.__doc__ or self._name)
        
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
        
        # Get whether function is a method
        try:
            self._func_is_method = inspect.getargspec(func)[0][0] in ('self', 'this')
        except (TypeError, IndexError):
            self._func_is_method = False
        
        # Check whether this signals is on a class object: a descriptor
        self._class_desciptor = (ob is None) and ('__module__' in self._frame.f_locals)
        
        # Check that for class descriptors the decorators are used
        if self._class_desciptor and frame is None:
            raise RuntimeError('On classes, signals cannot be instantiated directly; use the decorators.')
            
        # Init variables related to the signal value
        self._value = None
        self._last_value = None
        self._timestamp = 0
        self._last_timestamp = 0
        self._status = 3  # 0: ok, 1: out of date, 2: uninitialized, 3: unconnected
        
        # Connecting
        self._not_connected = 'No connection attempt yet.'
        self.connect(False)

    def __repr__(self):
        des = '-descriptor' if self._class_desciptor else ''
        conn = '(not connected)' if self.not_connected else 'with value %r' % self._value
        conn = '' if des else conn 
        return '<%s%s %r %s at 0x%x>' % (self.__class__.__name__, des, self._name, 
                                         conn, id(self))
    
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
        if instance is None:
            return self
        
        private_name = '_' + self._name + '_signal'
        try:
            return getattr(instance, private_name)
        except AttributeError:
            sys._getframe()
            frame = ObjectFrame(instance, self._frame.f_back)
            new = self.__class__(self._func, self._upstream_given, frame, ob=instance)
            setattr(instance, private_name, new)
            return new
    
    ## Connecting
    
    def connect(self, raise_on_fail=True):
        """ Connect input signals
        
        Signals that are provided as a string are resolved to get the
        signal object, and this signal subscribes to the upstream
        signals.
        
        If resolving the signals from the strings fails, raises an
        error. Unless ``raise_on_fail`` is False, in which case we return
        True on success.
        
        This function is automatically called during initialization,
        and when the value of this signal is obtained while the signal
        is not connected.
        
        """
        # First disconnect
        while len(self._upstream):  # len() for PyScript compat
            s = self._upstream.pop(0)
            s._unsubscribe(self)
        
        # Disable connecting for signal placeholders on classes
        if self._class_desciptor:
            #self.disconnect() we never connected. disconnect() would recurse 
            self._not_connected = 'Cannot connect signal descriptors on a class.'
            if raise_on_fail:
                raise RuntimeError(self._not_connected)
            return False
        
        # Resolve signals
        self._not_connected = self._resolve_signals()
        if self._not_connected:
            self._set_status(3)
            if raise_on_fail:
                raise RuntimeError('Connection error in signal %r: ' % self._name + self._not_connected)
            return False
        
        # Subscribe
        for signal in self._upstream:
            signal._subscribe(self)
        
        # Update status (also downstream)
        self._set_status(1)
    
    def disconnect(self):
        """ Disconnect this signal, unsubscribing it from the upstream
        signals. Note that if there is a react signal it will invoke a
        re-connect at once, which will immediately undo the
        disconnection if connecting succeeds.
        """
        # Disconnect upstream
        while len(self._upstream):  # len() for PyScript compat
            s = self._upstream.pop(0)
            s._unsubscribe(self)
        self._not_connected = 'Explicitly disconnected via disconnect()'
        # Notify downstream.
        self._set_status(3)
    
    def _resolve_signals(self):
        """ Get signals from their string path. Return value to store
        in _not_connected (False means success). Should only be called from
        connect().
        """
        
        upstream = []
        
        for fullname in self._upstream_given:
            nameparts = fullname.split('.')
            # Obtain first part of path from the frame that we have
            n = nameparts[0]
            ob = self._frame.f_locals.get(n, self._frame.f_globals.get(n, None))
            # Walk down the object tree to obtain the full path
            for name in nameparts[1:]:
                if ob is None:
                    break
                if isinstance(ob, Signal):
                    ob = ob()
                ob = getattr(ob, name, None)
            # Add to list or fail
            if ob is None:
                return 'Signal %r does not exist.' % fullname
            elif not isinstance(ob, Signal):
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
    def not_connected(self):
        """ False when not connected. Otherwise this is a string with
        a message why the signal is not connected.
        """
        return self._not_connected
    
    ## Getting and setting signal value
    
    def _save_update(self):
        """ Update our signal, when an error occurs, we print it and set
        sys.last_X for PM debugging, but return as usual.
        """
        try:
            self()
        except SignalValueError:
            pass
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
        self._status = 0
        if self._ob is not None:
            ob = self._ob()
            if hasattr(ob, '_signal_changed'):
                ob._signal_changed(self)
    
    def _get_value(self):
        """ Get the current value. Some overhead is put here to keep
        update_value compact.
        """
        if self._not_connected:
            self.connect(False)
        if self._status == 1:
            self._update_value()
        elif self._status == 2:
            raise SignalValueError('The signal is not initialized.')
        elif self._status == 3:
            raise SignalValueError('The signal is not connected.')
        return self._value
    
    def _update_value(self):
        """ Get the latest value from upstream. This method can be overloaded.
        """
        args = []  # todo: pyscript support for list comprehension
        for s in self._upstream:
            args.append(s())
        value = self._call_func(*args)
        self._set_value(value)
    
    def __call__(self, *args):
        """ Get the signal value.
        
        If the signals is not connected, raises SignalValueError. If an upstream
        signal is not connected, errr, what should we do?
        """
        if not args:
            return self._get_value()
        else:
            raise RuntimeError('Can only set signal values of InputSignal objects.')
    
    def _call_func(self, *args):
        if self._func_is_method and self._ob is not None:
            return self._func(self._ob(), *args)
        else:
            return self._func(*args)
    
    def _set_status(self, status, initiator=None):
        """ Called by upstream signals when their value changes.
        """
        # Prevent circular (stage 1: exit while our status is 0)
        initial_initiator = initiator
        if self is initial_initiator and not self._status:
            return
        if initiator is None:
            initiator = self
        # Calculate status from given status and upstream statuses
        # todo: pyscript comprehensions -> statuses = [s._status for s in self._upstream if s is not initiator]
        # statuses.extend([1, status])
        statuses = [1, status]
        for s in self._upstream:
            if s is not initiator:
                statuses.append(s._status)
        self._status = max(statuses)
        # Update self
        if self._active and self._status == 1:
            self._save_update()  # this can change our status to 0 or 2
        # Prevent circular (stage 2: exit with non-zero status)
        if self is initial_initiator:
            return
        # Allow downstream to update
        for signal in self._downstream:
            signal._set_status(status, initiator)


class SourceSignal(Signal):
    """ A signal that has no upstream signals, but produces values by itself.
    
    From the programmer's perspective, this is similar to an
    InputSignal, where the programmer sets the value with the ``_set()``
    method. Users of the signal should typically *not* use this private
    method.
    
    """
    _active = True

    def _update_value(self):
        # Try to initialize, func might not have a default value
        if self._timestamp == 0:
            ok = False
            try:
                value = self._call_func()
                ok = value is not undefined
            except Exception:
                pass
            if ok:
                self._set_value(value)
                return  # do not get from upstream initially
            else:
                self._status = 2
                self._last_timestamp = self._timestamp
                self._timestamp = 1
        # Get value from upstream, can raise SignalValueError
        if len(self._upstream):  # len() for PyScript compat
            # args = [s() for s in self._upstream]
            args = [self._value]  # todo: pyscript support for list comprehension
            for s in self._upstream:
                args.append(s())  # can raise SignalValueError
            value = self._call_func(*args)
            self._set_value(value)
    
    def _set(self, value):
        """ Method for the developer to set the source signal.
        """
        self._set_value(self._call_func(value))
        for signal in self._downstream:
            signal._set_status(1, self)  # do not set status of *this* signal!


class InputSignal(SourceSignal):
    """ InputSignal objects are special signals for which the value can
    be set by the user, by calling the signal with a single argument.
    
    The function associated with the signal is used to validate the
    use-specified value.
    
    """
    
    def __call__(self, *args):
        if not args:
            return self._get_value()
        elif len(args) == 1:
            return self._set(args[0])
        else:
            raise ValueError('Setting an input signal requires exactly one argument')


class WatchSignal(Signal):
    pass


class ActSignal(Signal):
    """ A signal that reacts immediately to changes of upstream signals.
    """ 
    _active = True


class PropSignal(InputSignal):
    def __set__(self, obj, value):
        
        if obj is None:
            raise ValueError('Cannot overwrite a signal; use some_signal(val) on InputSignal objects.')
        
        s = InputSignal.__get__(self, obj, None)
        s(value)
    
    def __get__(self, obj, owner):
        s = InputSignal.__get__(self, obj, None)
        if obj:
            return s()
        else:
            return s


class HasSignalsMeta(type):
    """ Meta class for HasSignals
    * Set the name of each signal
    * Sets __signals__ attribute on the class
    """
    
    CLASSES = []
    
    def __init__(cls, name, bases, dct):
        
        HasSignalsMeta.CLASSES.append(cls)  # todo: dict by full qualified name?
        
        # Collect signals defined on this class
        signals = {}
        props = {}
        for name in dir(cls):
            if name.startswith('__'):
                continue
            val = getattr(cls, name)
            if isinstance(val, type) and issubclass(val, Signal):
                val = val()
                setattr(cls, name, val)  # allow setting just class
            if isinstance(val, Signal):
                signals[name] = val
                if isinstance(val, PropSignal):
                    props[name] = val
        # Finalize all found props
        for name, signal in signals.items():
            signal._name = name
        # Cache prop names
        cls.__signals__ = [name for name in sorted(signals.keys())]
        cls.__props__ = [name for name in sorted(props.keys())]
        # Proceeed as normal
        type.__init__(cls, name, bases, dct)


class HasSignals(with_metaclass(HasSignalsMeta, object)):
    """ A base class for objects with signals.
    
    Creating signals on this class will provide each instance of this
    class to have corresponding signals. During initialization the
    signals are connected, and this class has a ``connect_signals()``
    method to easily allow connecting any unconnected signals at a
    latere time.
    
    Upstream signal names can be attributes on the instance, as well
    as variables in the scope in which the class was defined.
    
    Note that signals can be attached to any class, but then each signal
    will have to be "touched" to create the signal instance, and the
    signals might not be initially connected.
    
    Functions defined on this class that are wrapped by signals can
    have a ``self`` argument, but this is not mandatory.
    """
    
    def __init__(self):
        
        # Instantiate signals, its enough to reference them
        for name in self.__class__.__signals__:
            #val = getattr(self.__class__, name)
            getattr(self, name)
        
        self.connect_signals(False)
    
    def connect_signals(self, raise_on_fail=True):
        """ Connect any disconnected signals associated with this object.
        """
        success = True
        for name in self.__signals__:
            if name in self.__props__:
                continue
            s = getattr(self, name)
            if s.not_connected:
                connected = s.connect(raise_on_fail)  # dont combine this with next line
                success = success and connected
        return success
    
    
    def _signal_changed(self, signal):
        """ Called when one of our signals changes.
        Can be used to do more signal magic.
        """
        pass


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
    frame = sys._getframe(1)
    def _source(func):
        return SourceSignal(func, input_signals, frame=frame)
    
    if _first_arg_is_func(input_signals):
        func, input_signals = input_signals[0], []
        return _source(func)
    else:
        return _source


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
    frame = sys._getframe(1)
    def _input(func):
        return InputSignal(func, input_signals, frame=frame)
    
    if _first_arg_is_func(input_signals):
        func, input_signals = input_signals[0], []
        return _input(func)
    else:
        return _input


def prop(*input_signals):
    """ Decorator to transform a function into a InputSignal object.
   
    """
    frame = sys._getframe(1)
    def _prop(func):
        return PropSignal(func, input_signals, frame=frame)
    
    if _first_arg_is_func(input_signals):
        func, input_signals = input_signals[0], []
        return _prop(func)
    else:
        return _prop


def watch(*input_signals):
    """ Decorator to transform a function into a Signal object.
    
    A signal takes one or more signals as input (specified as arguments
    to this decorator) and produces a new signal value. The function
    being wrapped should have an argument for each upstream signal, and
    its return value is used as the output signal value.
    
    Example:
    
        @watch('s1', 's2')
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
        s = WatchSignal(func, input_signals, frame=frame)
        return s
    return _signal    


def act(*input_signals):
    """ Decorator to transform a function into a ReactSignal object.
    
    A react signal takes one or more signals as input (specified as
    arguments to this decorator) and may produce a new signal value.
    The function being wrapped should have an argument for each upstream
    signal, and its return value is used as the output signal value.
    The ReactSignal is commonly used for end-signals, which require no
    output signal.
    
    Example:
    
        @act('s1', 's2')
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
        s = ActSignal(func, input_signals, frame=frame)
        return s
    return _react
