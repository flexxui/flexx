"""
Implements the different signal classes.
"""

import sys
import time
import inspect
import weakref
import logging


if sys.version_info >= (3, ):
    string_types = str
else:  # pragma: no cover
    string_types = basestring


# Get global version of "undefined", so we can use ``is`` operator.
class undefined:
    def __repr__(self): return 'undefined'
undefined = getattr(sys, '_undefined', undefined())


class SignalValueError(Exception):
    pass


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
    """ A Signal is an object that provides a value that changes over time.
    The current value can be obtained by calling the signal object or via
    the ``.value`` attribute.
    
    This class should not be instantiated directly; use the decorators instead.
    """
    _IS_SIGNAL = True  # poor man's isinstance in JS (because class name mangling)
    _active = True
    
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
            assert isinstance(s, string_types) or isinstance(s, Signal)
        self._upstream_given = [s for s in upstream]
        self._upstream = []
        self._downstream = []
        self._upstream_reconnect = []
        self._downstream_reconnect = []
        
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
            raise RuntimeError('On classes, signals cannot be instantiated directly; '
                               'use the decorators. (%r)' % self._name)
            
        # Init variables related to the signal value
        self._value = undefined
        self._last_value = undefined
        self._count = 0
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
        """ The name of this signal, usually corresponding to the name
        of the function that this signal wraps.
        """
        return self._name
    
    ## Behavior for when attached to a class
    
    def __set__(self, obj, value):
        raise ValueError('Cannot overwrite signal %r; use some_signal(val) on '
                         'InputSignal objects.' % self._name)
    
    def __delete__(self, obj):
        raise ValueError('Cannot delete signal %r.' % self._name)
    
    def __get__(self, instance, owner):
        if instance is None:
            return self
        
        private_name = '_' + self._name + '_signal'
        try:
            return getattr(instance, private_name)
        except AttributeError:
            sys._getframe()
            frame = ObjectFrame(instance, self._frame.f_back)
            new = self.__class__(self._func, self._upstream_given, frame, instance)
            setattr(instance, private_name, new)
            return new
    
    ## Connecting
    
    def connect(self, raise_on_fail=True):
        """ Connect input signals
        
        The upstream signals that were provided as a string are resolved
        to get the signal objects, and the current signal is subscribed
        to these signals.
        
        If resolving the signals from the strings fails, raises an
        error. Unless ``raise_on_fail`` is ``False``, in which case this
        returns ``True`` on success and ``False`` on failure.
        
        This function is automatically called during initialization,
        and when the value of this signal is obtained while the signal
        is not connected.
        """
        # First disconnect
        while len(self._upstream):  # len() for PyScript compat
            s = self._upstream.pop(0)
            s._unsubscribe(self)
        while len(self._upstream_reconnect):  # len() for PyScript compat
            s = self._upstream_reconnect.pop(0)
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
        
        # Subscribe (on a fail, the _upstream_reconnect can be non-empty
        for signal in self._upstream:
            signal._subscribe(self)
        for signal in self._upstream_reconnect:
            signal._subscribe(self, True)
        
        # Fail?
        if self._not_connected:
            self._set_status(3)
            if raise_on_fail:
                raise RuntimeError('Connection error in signal %r: ' % self._name + self._not_connected)
            return False
        
        # Update status (also downstream)
        self._set_status(1)
        return True
    
    def disconnect(self):
        """ Disconnect this signal, unsubscribing it from the upstream
        signals.
        """
        # Disconnect upstream
        while len(self._upstream):  # len() for PyScript compat
            s = self._upstream.pop(0)
            s._unsubscribe(self)
        self._not_connected = 'Explicitly disconnected via disconnect()'
        # Notify downstream.
        self._set_status(3)
    
    def _seek_signal(self, fullname, nameparts, ob):
        """ Seek a signal based on the name. Used by _resolve_signals.
        This bit is PyScript compatible (_resolve_signals is not).
        """
        # Done traversing name: add to list or fail
        if ob is undefined or len(nameparts) == 0:
            if ob is undefined:
                return 'Signal %r does not exist.' % fullname
            if not hasattr(ob, '_IS_SIGNAL'):
                return 'Object %r is not a signal.' % fullname
            self._upstream.append(ob)
            return None  # ok
        # Get value if ob is a signal
        if hasattr(ob, '_IS_SIGNAL'):
            self._upstream_reconnect.append(ob)
            try:
                ob = ob()
            except SignalValueError:
                return 'Signal %r does not have all parts ready' % fullname  # we'll rebind when that signal gets a value
        # Resolve name
        name, nameparts = nameparts[0], nameparts[1:]
        if name == '*' and isinstance(ob, (tuple, list)):
            for sub_ob in ob:
                msg = self._seek_signal(fullname, nameparts, sub_ob)
                if msg:
                    return msg
            return None  # ok
        return self._seek_signal(fullname, nameparts, getattr(ob, name, undefined))
    
    def _resolve_signals(self):
        """ Get signals from their string path. Return value to store
        in _not_connected (False means success). Should only be called from
        connect().
        """
        
        self._upstream = []
        self._upstream_reconnect = []
        
        for fullname in self._upstream_given:
            if getattr(fullname, '_IS_SIGNAL', False):
                self._upstream.append(fullname)
                continue
            nameparts = fullname.split('.')
            # Obtain first part of path from the frame that we have
            n = nameparts[0]
            ob = self._frame.f_locals.get(n, self._frame.f_globals.get(n, undefined))
            msg = self._seek_signal(fullname, nameparts[1:], ob)
            if msg:
                self._upstream = []
                return msg
        
        return False  # no error
    
    def _subscribe(self, signal, reconnect=False):
        """ For a signal to subscribe to this signal.
        """
        if reconnect:
            if signal not in self._downstream_reconnect:
                self._downstream_reconnect.append(signal)
        else:
            if signal not in self._downstream:
                self._downstream.append(signal)
    
    def _unsubscribe(self, signal):
        """ For a signal to unsubscribe from this signal.
        """
        while signal in self._downstream:
            self._downstream.remove(signal)
        while signal in self._downstream_reconnect:
            self._downstream_reconnect.remove(signal)
    
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
        """ The previous signal value, corresponding to the value right
        before the last time that the signal was updated.
        """
        return self._last_value
    
    def _set_value(self, value):
        """ This is like ``self._value = value``, but with bookkeeping.
        """
        if value is undefined:
            self._status = 3 if (self._count == 0) else 0
            return  # new tick, but no update of value
        self._last_value = self._value
        self._value = value
        self._count += 1
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
            raise SignalValueError('The signal %r is not initialized.' % self._name)
        elif self._status == 3:
            raise SignalValueError('The signal %r is not connected.' % self._name)
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
        
        If the signal (or any of its upstream signals) is not connected,
        raises ``SignalValueError``.
        """
        if not args:
            return self._get_value()
        else:
            raise RuntimeError('Can only set signal values of InputSignal objects, '
                               'which signal %r is not.' % self._name)
    
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
        if self._name == 'number2':
            pass
        if self._active and self._status == 1:
            count = self._count
            self._save_update()  # this can change our status to 0 or 2 or 3
            if self._count == count:
                return  # value was not updated (undefined)
        # Prevent circular (stage 2: exit with non-zero status)
        if self is initial_initiator:
            return
        # Allow downstream to update
        for signal in self._downstream_reconnect[:]:  # list may be modified
            signal.connect(False)
        for signal in self._downstream:
            signal._set_status(status, initiator)


class SourceSignal(Signal):
    """ A signal that typically has no upstream signals, but produces
    values by itself.
    """

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
        value = self._call_func(value)
        self._set_value(value)
        if value is undefined:
            return  # no need to update
        for signal in self._downstream_reconnect[:]:  # list may be modified
            signal.connect(False)
        for signal in self._downstream:
            signal._set_status(1, self)  # do not set status of *this* signal!


class InputSignal(SourceSignal):
    """ A signal that typically has no upstream signals, but produces
    values from user input (by calling the signal object with the new
    value).
    """
    
    def __call__(self, *args):
        if not args:
            return self._get_value()
        elif len(args) == 1:
            return self._set(args[0])
        else:
            raise ValueError('Setting an input signal (%r) requires exactly one argument' % self._name)


class PropSignal(InputSignal):
    """ A signal which value can be get/set by the user using assignment.
    
    Supported, but not really recommended, see the ``prop()`` function.
    """
    
    def __set__(self, obj, value):
        
        if obj is not None:
            s = InputSignal.__get__(self, obj, None)
            s(value)
    
    def __get__(self, obj, owner):
        s = InputSignal.__get__(self, obj, None)
        if obj:
            return s()
        else:
            return s


class LazySignal(Signal):
    """ A signal that does *not* immediately update, but instead queries
    the latest upstream values at the last moment.
    """
    _active = False
