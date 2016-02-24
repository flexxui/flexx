"""
Definition of descriptors for generating events: prop, readonly and emitter.
"""

import inspect


# Decorators to apply at a EventEmitter class

def prop(func):
    return Property(func)

def readonly(func):
    return Readonly(func)

def emitter(func):
    return Emitter(func)


class EventGenerator:
    """ Base class for descriptors used for generating events.
    """
    
    _IS_EVENT_GENERATOR = True

    def __init__(self, func):
        if not callable(func):
            raise ValueError('%s needs a callable' % self.__class__.__name__)
        self._func = func
        self._name = func.__name__  # updated by EventEmitter meta class
        self._is_being_set = False
        self.__doc__ = '*%s*: %s' % (self.__class__.__name__.lower(),
                                     func.__doc__ or self._name)
        
        # Get whether function is a method
        try:
            self._func_is_method = inspect.getargspec(func)[0][0] in ('self', 'this')
        except (TypeError, IndexError):
            self._func_is_method = False
    
    def __repr__(self):
        cls_name = self.__class__.__name__
        return '<%s for %s at 0x%x>' % (cls_name, self._name, id(self))


class Property(EventGenerator):
    """ A value that is gettable and settable.
    """
    
    _IS_PROP = True
    _SUFFIX  = '_value'
    
    
    def __set__(self, instance, value):
        if isinstance is not None:
            return self._set(instance, value)
    
    def __delete__(self, instance):
        raise AttributeError('Cannot delete property %r.' % self._name)
    
    def __get__(self, instance, owner):
        if instance is None:
            return self
        
        private_name = '_' + self._name + self._SUFFIX
        try:
            return getattr(instance, private_name)
        except AttributeError:
            return self._set_default(instance)
    
    def _set(self, instance, value):
        if self._is_being_set:
            return
        private_name = '_' + self._name + self._SUFFIX
        # Validate value
        self._is_being_set = True
        try:
            if self._func_is_method:
                value2 = self._func(instance, value)
            else:
                value2 = self._func(value)
        except Exception as err:
            raise
        finally:
            self._is_being_set = False
        # Update value and emit event
        old = getattr(instance, private_name, None)
        setattr(instance, private_name, value2)
        instance.emit(self._name, dict(new_value=value2, old_value=old))
    
    def _set_default(self, instance):
        if self._is_being_set:
            return
        private_name = '_' + self._name + self._SUFFIX
        # Trigger default value
        self._is_being_set = True
        try:
            if self._func_is_method:
                value2 = self._func(instance)
            else:
                value2 = self._func()
        except Exception as err:
            raise RuntimeError('Could not get default value for property %r' % self._name)
        finally:
            self._is_being_set = False
        # Update value and emit event
        old = None
        setattr(instance, private_name, value2)
        instance.emit(self._name, dict(new_value=value2, old_value=old))
        return value2


class Readonly(Property):
    """ A value that is gettable and only settable internally.
    """
    
    def __set__(self, instance, value):
        raise AttributeError("Can't set readonly property %r" % self._name)


# todo: names ... arg
class Emitter(EventGenerator):
    """ Placeholder for documentation and easy emitting of the event.
    """
    
    def __set__(self, instance, value):
        raise AttributeError("Can't set emitter attribute %r" % self._name)
    
    def __delete__(self, instance):
        raise AttributeError('Cannot delete emitter attribute %r.' % self._name)
    
    def __get__(self, instance, owner):
        if instance is None:
            return self
        
        def emitter_func(value):
            if self._func_is_method:
                ev = self._func(instance, value)
            else:
                ev = self._func(value)
            instance.emit(self._name, ev)
        emitter_func.__doc__ = self.__doc__
        return emitter_func
