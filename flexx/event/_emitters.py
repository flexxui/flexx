"""
Implementation of descriptors for generating events:
prop, readonly and emitter.
"""

import inspect


# Decorators to apply at a HasEvents class

def prop(func):
    """ Decorator to define a settable propery. An event is emitted
    when the property is set, which has values for "old_value" and
    "new_value".
    
    .. code-block:: python
    
        class MyObject(event.HasEvents):
           
           @prop
           def foo(self, v=1):
                ''' docstring goes here. '''
                return float(v)
        
        m = MyObject(foo=2)
        m.foo = 3
    
    The method should have one argument, which can have a default
    value to specify the initial value of the property. The body
    of the method is used to do verification and normalization of the
    value being set. The method's docstring is used as the property's
    docstring.
    """
    if not callable(func):
        raise TypeError('prop decorator needs a callable')
    return Property(func)


def readonly(func):
    """ Decorator to define a readonly property. An event is emitted
    when the property is set, which has values for "old_value" and
    "new_value". To set a readonly property internally, use the
    :func:`HasEvents._set_prop() <flexx.event.HasEvents._set_prop>` method.
    
    .. code-block:: python
    
        class MyObject(event.HasEvents):
           
           @readonly
           def bar(self, v=1):
                return float(v)
        
        m = MyObject()
        m._set_prop('bar', 2)  # only for internal use
    
    """
    if not callable(func):
        raise TypeError('readonly decorator needs a callable')
    return Readonly(func)


def emitter(func):
    """ Decorator to define an emitter. An emitter is an attribute that
    makes it easy to emit specific events and functions as a placeholder
    for documenting an event.
    
    .. code-block:: python
    
        class MyObject(event.HasEvents):
           
           @emitter
           def spam(self, v):
                return dict(value=v)
        
        m = MyObject()
        m.spam(42)
    
    The method can have any number of arguments, and should return a
    dictionary that represents the event to generate. The method's
    docstring is used as the emitter's docstring.
    """
    if not callable(func):
        raise TypeError('emitter decorator needs a callable')
    return Emitter(func)


class BaseEmitter:
    """ Base class for descriptors used for generating events.
    """
    
    def __init__(self, func, name=None, doc=None):
        assert callable(func)
        self._func = func
        self._name = name or func.__name__  # updated by HasEvents meta class
        self.__doc__ = '*%s*: %s' % (self.__class__.__name__.lower(),
                                     doc or func.__doc__ or self._name)
    
    def __repr__(self):
        cls_name = self.__class__.__name__
        return '<%s for %s at 0x%x>' % (cls_name, self._name, id(self))
    
    def get_func(self):
        """ Get the corresponding function object.
        """
        return self._func


class Property(BaseEmitter):
    """ A value that is gettable and settable.
    """
    
    _SUFFIX = '_value'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._defaults = inspect.getargspec(self._func).defaults
        # defaults is a list, so we can see if there is a default (it might be None)
    
    def __set__(self, instance, value):
        if instance is not None:  # pragma: no cover
            return instance._set_prop(self._name, value)
    
    def __delete__(self, instance):
        raise AttributeError('Cannot delete property %r.' % self._name)
    
    def __get__(self, instance, owner):
        if instance is None:
            return self
        private_name = '_' + self._name + self._SUFFIX
        return getattr(instance, private_name)


class Readonly(Property):
    """ A value that is gettable and only settable internally.
    """
    
    def __set__(self, instance, value):
        raise AttributeError("Can't set readonly property %r" % self._name)


class Emitter(BaseEmitter):
    """ Placeholder for documentation and easy emitting of the event.
    """
    
    def __set__(self, instance, value):
        raise AttributeError("Can't set emitter attribute %r" % self._name)
    
    def __delete__(self, instance):
        raise AttributeError('Cannot delete emitter attribute %r.' % self._name)
    
    def __get__(self, instance, owner):
        if instance is None:
            return self
        def func(*args):  # this func should return None, so super() works correct
            ev = self._func(instance, *args)
            if ev is not None:
                instance.emit(self._name, ev)
        func.__doc__ = self.__doc__
        return func
