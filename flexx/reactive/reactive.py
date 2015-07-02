"""
Signals and reactions, the Functional Reactive Programming approach to events.

How this works
--------------

On subclasses of Reactor, Signal objects can be attached, either directly
or via the ``@react`` decorator. These signals are converted to
SignalProp objects on the class by the meta class. The signalprop
"serves" (via ``__get__``) the actual signal, which is created in the
__init__, using the original signal as a template.

Signals need to be initialized with a) a function; b) a list of signals
it depends on; c) the stack frame to look up names (optional).
Dependencies can be given as string names, which will be looked up when
binding the signal. In the init of HasProps, all signals are first created
and then bound; signals may depend on each-other.

The stack frame is provided using ``sys._getframe()``, which is why
this only works on Python implementations *with* a stack.

In JS, signals by name can only be applied for signals attached on
Reactor objects.
"""


"""

THINGS I FEEL UNCONFORTABLE ABOUT

* signal binding fails silently. But maybe is ok, because you cannot know the
  time when the binding is supposed to work. Also the unbound attribute should
  show what's wrong.
* signal name is derived from func, which might be a lambda or buildin.
* Stray signals on classes ... ?

QUESTIONS / TODO

* serializing signal values to json, maybe support base types and others need
  a __json__ function.
* Predefined inputs? Str, Int, etc?
* DONE When binding, update
* Binding is now simple and predictable, should we be smarter?
  For instance by binding unbound signals in the same frame when calling?

"""

import sys
import inspect
import weakref
import logging

string_types = str  # todo: six


class UnboundError(Exception):
    def __init__(self, msg='This signal is not bound.'):
        Exception.__init__(self, msg)


class FakeFrame(object):
    """ Simulate an object as a frame, to fool Signal.
    """
    def __init__(self, ob, globals):
        self._ob = weakref.ref(ob)
        self._globals = globals
    
    @property
    def f_locals(self):
        ob = self._ob() 
        if ob is not None:
            locals = ob.__dict__.copy()
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
    
    def __init__(self, func, upstream, _frame=None, _ob=None):
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
        self._frame = _frame or sys._getframe(1)
        self._ob = weakref.ref(_ob) if (_ob is not None) else lambda x=None: None
        
        # Get whether function is bound
        try:
            self._func_is_bound = inspect.getargspec(func)[0][0] in ('self', 'this')
        except (TypeError, IndexError):
            self._func_is_bound = False
        
        # Init variables related to the signal value
        self._value = None
        self._dirty = True
        
        # Flag to indicate that this is a class desciptor, and should not be used
        self._class_desciptor = None
        if self._func_is_bound and _ob is None:
            self._class_desciptor = True
        
        # Binding
        self._unbound = 'No binding attempted yet.'
        self.bind(ignore_fail=True)

    def __repr__(self):
        # todo: should not error!
        des = '-descriptor' if self._class_desciptor else ''
        bound = '(unbound)' if self.unbound else 'with value %r' % self._value
        return '<%s%s %r %s at 0x%x>' % (self.__class__.__name__, des, self._name, 
                                       bound, id(self))

    ## Behavior for when attaches to a class
    
    def __set__(self, obj, value):
        raise ValueError('Cannot overwrite a signal; use some_signal(val) on InputSignal objects.')
    
    def __delete__(self, obj):
        raise ValueError('Cannot delete a signal.')
    
    def __get__(self, instance, owner):
        if not self._class_desciptor:
            self._class_desciptor = True
            self.bind(True)  # trigger unsubscribe
        if instance is None:
            return self
        
        private_name = '_' + self._name
        try:
            return getattr(instance, private_name)
        except AttributeError:
            new = self._new_instance(instance)
            setattr(instance, private_name, new)
            return new
    
    def _new_instance(self, _self):
        # if isinstance(self, InputSignal):
        #     ob = self.__class__(self._func)
        # else:
        ob = self.__class__(self._func, self._upstream_given, FakeFrame(_self, self._frame.f_globals), _ob=_self)
        return ob
    
    
    ## Binding
    
    
    def bind(self, ignore_fail=False):
        """ Bind input signals
        
        Signals that are provided as a string are resolved to get the
        signal object, and this signal subscribes to the upstream
        signals.
        
        If resolving the signals from the strings fails, raises an
        error. Unless ``ignore_fail`` is True, in which case we return
        True on success.
        """
        
        # Disable binding for signal placeholders on classes
        if self._class_desciptor:
            self.unbind()
            self._unbound = 'Cannot bind signal descriptors on a class.'
            if ignore_fail:
                return False
            raise RuntimeError(self._unbound)
        
        # Resolve signals
        self._unbound = self._resolve_signals()
        if self._unbound:
            if ignore_fail:
                return False
            else:
                raise ValueError('Bind error in signal %r: ' % self._name + self._unbound)
        
        # Subscribe
        for signal in self._upstream:
            signal._subscribe(self)
        
        # If binding complete, set value
        self._save_update()
    
    def unbind(self):
        """ Unbind this signal, unsubscribing it from the upstream signals.
        """
        while self._upstream:
            s = self._upstream.pop(0)
            s._unsubscribe(self)
    
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
        """ The signal value. 
        """
        return self()
    
    @property
    def last_value(self):
        """ The previous signal value. 
        """
        pass # todo: last value
    
    def __call__(self, *args):
        """ Get the signal value.
        
        If the signals is unbound, raises UnBoundError. If an upstream
        signal is unbound, errr, what should we do?
        """
        
        if self._unbound:
            self.bind(True)
        
        # todo: what to do when an upstream signal (or upstream-upstream) is unbound?
        if not args:
            # Update value if necessary, then return it
            if self._unbound:
                raise UnboundError()
            if self._dirty:
                self._dirty = False
                try:
                    args2 = [s() for s in self._upstream]
                except UnboundError:
                    self._dirty = True
                    return self._value
                self._value = self._call(*args2)
            return self._value
        else:
            raise RuntimeError('Can only set signal values of InputSignal objects.')
    
    def _call(self, *args):
        if self._func_is_bound:
            return self._func(self._ob(), *args)
        else:
            return self._func(*args)
    
    def _set_dirty(self, initiator):
        """ Called by upstream signals when their value changes.
        """
        if self is initiator:
            return
        # Update self
        self._dirty = True
        # Allow downstream to update
        for signal in self._downstream:
            signal._set_dirty(initiator)
        # Note: we do not update our value now; lazy evaluation. See
        # the ReactSignal for pushing changes downstream immediately.
    

# todo: rename to Input
class InputSignal(Signal):
    """ InputSignal objects are special signals for which the value can
    be set by the user, by calling the signal with a single argument.
    
    The function associated with the signal is used to validate the
    use-specified value.
    
    """
    
    def __init__(self, func, upstream=[], _frame=None, _ob=None):
        self._in_init = True
        Signal.__init__(self, func, upstream, _frame, _ob)
        self._dirty = False
        self._in_init = False
        try:
            self._value = self._call()
        except Exception:
            pass  # maybe does not handle default values
    
    def __call__(self, *args):
        
        if self._unbound:
            self.bind(True)
        
        if not args:
            if self._unbound:
                raise UnboundError()
            # Update value if necessary, then return it
            if self._dirty:
                self._dirty = False
                if self._in_init:
                    # Try to initialize
                    try:
                        self._value = self._call()
                    except Exception:
                        pass  # maybe does not handle default values
                if self._upstream:
                    try:
                        args2 = [self._value] + [s() for s in self._upstream]
                    except UnboundError:
                        self._dirty = True
                        return self._value
                    self._value = self._call(*args2)
            return self._value
        
        elif len(args) > 1:
            raise TypeError('Setting (i.e. calling an input signal needs 1 argument.')
        
        else:
            # Set the signal value
            self._value = self._call(args[0])
            self._dirty = False
            for signal in self._downstream:
                signal._set_dirty(self)
    
    def _set_dirty(self, initiator):
        # An input signal that has upstream signals is reactive too.
        Signal._set_dirty(self, initiator)
        self._save_update()


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
    """
    
    def __init__(self):
        
        # Instantiate signals, its enough to reference them
        self.__signals__ = []
        for key, val in sorted(self.__class__.__dict__.items()):
            if isinstance(val, Signal):
                getattr(self, key)
                self.__signals__.append(key)
        
        self.bind_unbound(True)
    
    def bind_unbound(self, ignore_fail=False):  # todo: reverse/rename to fail_hard
        """ Bind any unbound signals associated with this object.
        """
        success = True
        for name in self.__signals__:
            s = getattr(self, name)
            if s.unbound:
                print('unbound', s)
                bound = s.bind(ignore_fail)  # dont combine this with next line
                success = success and bound
        return success


def _first_arg_is_func(ii):
    return len(ii) == 1 and (not isinstance(ii[0], Signal)) and callable(ii[0])


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
        # todo: create dummy frame
        s = InputSignal(func)
        return s
    def _input_with_signals(func):
        frame = sys._getframe(1)
        s = InputSignal(func, input_signals, _frame=frame)
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
        s = Signal(func, input_signals, _frame=frame)
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
        s = ReactSignal(func, input_signals, _frame=frame)
        return s
    return _react



## =====================================
# Test

# 
# class Foo(HasSignals):
#     
#     def __init__(self):
#         HasSignals.__init__(self)
#         self.b = HasSignals()
#         self.b.title = InputSignal(float)
#         self.bind_unbound(True)
#     
#     @input
#     def title(v=''): return str(v)
#     
#     @input
#     def age(v=0): return int(v)
#     
#     @input
#     def weirdInt(self, value=0):
#         if value < 0:
#             raise ValueError('weird Int must be above zero')
#         return value
#     
#     @react('title', 'X')
#     #@react('name', 'age')
#     def name_length1(self, name, y):
#         return len(name)  # todo: can do this with just "len"?
#     
#     @react('title', 'Y')
#     #@react('name', 'age')
#     def name_length2(self, name, y):
#         return len(name)  # todo: can do this with just "len"?
#     
#     @react('name_length1')
#     def update_something(self, v):
#         print('title/name has length', v)
#     
#     @react('b.title')
#     def subtitle(v):
#         print('subtitle is', v)
# 
# X = InputSignal(str)
# 
# foo = Foo()
# 
# Y = InputSignal(str)
# 
# @react('foo.titles')
# def as_in_name(name):
#     return name.count('a')
# 
# 
# class Temperature(HasSignals):
#     """ Example of object that allows the user to get/set temperature
#     in both Celcius and Fahrenheit. Example from the Trellis project.
#     """
#     
#     @input('F')
#     def C(v=32, f=None):
#         if f is None:
#             return float(v)
#         else:
#             return (f - 32)/1.8
#     
#     @input('C')
#     def F(v=0, c=None):
#         if c is None:
#             return float(v)
#         else:
#             return c * 1.8 + 32
#             
#     
#     @react('C')
#     def show(self, c):
#         print('degrees Celcius: %1.2f' % self.C())
#         print('degrees Fahrenheit: %1.2f' % self.F())
# 
# t = Temperature()


