"""
Implements the HasSignals class (and its meta class).
"""

from .signals import Signal, PropSignal


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
    class with corresponding signal objects. During initialization the
    signals are connected, and this class has a ``connect_signals()``
    method to easily allow connecting any unconnected signals at a
    later time.
    
    Upstream signal names can be attributes on the instance, as well
    as variables in the scope in which the class was defined.
    
    Note that signals can be attached to any class, but then each signal
    will have to be "touched" to create the signal instance, and the
    signals might not be initially connected.
    
    Functions defined on this class that are lifted to signals can
    have a ``self`` argument, but this is not mandatory.
    """
    
    def __init__(self, **initial_signal_values):
        
        # Instantiate signals, its enough to reference them
        for name in self.__class__.__signals__:
            #val = getattr(self.__class__, name)
            getattr(self, name)
        
        self.connect_signals(False)
        
        for name, val in initial_signal_values.items():
            if name not in self.__class__.__signals__:
                raise ValueError('Object does not have a signal %r' % name)
            signal = getattr(self, name)
            signal(val)
    
    def connect_signals(self, raise_on_fail=True):
        """ Connect any disconnected signals associated with this object.
        """
        success = True
        for name in self.__class__.__signals__:
            if name in self.__class__.__props__:
                continue
            s = getattr(self, name)
            if s.not_connected:
                connected = s.connect(raise_on_fail)  # dont combine this with next line
                success = success and connected
        return success
    
    def disconnect_signals(self, destroy=True):
        """ Disconnect all signals. This can be used to clean up any
        references when the object is no longer used.
        """
        for name in self.__signals__:
            if name in self.__props__:
                continue
            s = getattr(self, name)
            s.disconnect(destroy)
    
    def _signal_changed(self, signal):
        """ Called when one of our signals changes.
        Can be used to do more signal magic.
        """
        pass
