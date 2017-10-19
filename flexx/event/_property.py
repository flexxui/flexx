"""
Implements the property decorator, class and desciptor.
"""

import inspect

from ._loop import loop
from ._action import BaseDescriptor


class Property(BaseDescriptor):
    """ Class descriptor for properties.
    """
    
    def __init__(self, default=None, doc='', settable=None):
        if callable(default):
            raise TypeError('event.prop() is not a decorator (anymore).')
        if not isinstance(doc, str):
            raise TypeError('event.prop() doc must be a string.')
        if not (settable is None or settable is True or callable(settable)):
            raise TypeError('event.prop() settable must be None, True, or callable.')
            
        self._default = default
        self._settable = settable
        self._doc = doc
        self._set_name('anonymous_property')
    
    def _set_name(self, name):
        self._name = name  # or func.__name__
        self.__doc__ = '*property*: %s' % (self._doc or self._name)
                                     
    def __set__(self, instance, value):
        t = 'Cannot set property %r; properties can only be mutated by actions.'
        raise AttributeError(t % self._name)
    
    def __get__(self, instance, owner):
        if instance is None:
            return self
        private_name = '_' + self._name + '_value'
        loop.register_prop_access(instance, self._name)
        return getattr(instance, private_name)
    
    def make_mutator(self):
        name = self._name
        def mutator(self, *args):
            return self._mutate(name, *args)
        return mutator
    
    def make_set_action(self):
        name = self._name
        func = self._settable
        if func is True:
            func = lambda x: x
        def setter(self, *args):
            self._mutate(name, func(*args))
        return setter
    
    def _validate(self, value):
        raise NotImplementedError('Cannot use Property; use one of the subclasses instead.')


# todo: these need docs!

class AnyProp(Property):
    
    def _validate(self, value):
        return value


# todo: this is useless unless combined with AnyProp
class NullProp(Property):
    
    def _validate(self, value):
        if not isinstance(value, None):
            raise TypeError('Null property can only be None.')


class BoolProp(Property):
    
    def _validate(self, value):
        return bool(value)


class IntProp(Property):
    
    def _validate(self, value):
        return int(value)


class FloatProp(Property):
    
    def _validate(self, value):
        return float(value)


class StringProp(Property):
    
    def _validate(self, value):
        if not isinstance(value, str):
            raise TypeError('%s property cannot accept %s.' %
                            (self.__class__.__name__, value.__class__.__name__))
        return value


class TupleProp(Property):
    
    def _validate(self, value):
        if not isinstance(value, (tuple, list)):
            raise TypeError('%s property cannot accept %s.' %
                            (self.__class__.__name__, value.__class__.__name__))
        return tuple(value)


# todo: test in both that initializing a prop gives a new list instance
class ListProp(Property):
    
    def _validate(self, value):
        if not isinstance(value, (tuple, list)):
            raise TypeError('%s property cannot accept %s.' %
                            (self.__class__.__name__, value.__class__.__name__))
        return list(value)


# todo: can I make this work on JS?
class EitherProp(Property):
    
    def __init__(self, *prop_classes, **kwargs):
        self._sub_classes = prop_classes
    
    def _validate(self, value):
        for cls in self._sub_classes:
            try:
                return cls._validate(self, value)
            except TypeError:
                pass
            raise TypeError('This %s property cannot accept %s.' %
                            (self.__class__.__name__, value.__class__.__name__))

class ComponentProp(Property):
    
    def _validate(self, value):
        from ._component import Component
        if not (value is None or isinstance(value, Component)):
            raise TypeError('%s property cannot accept %s.' %
                            (self.__class__.__name__, value.__class__.__name__))
        return value


## More special

# class Auto -> Bokeh has special prop to indicate "automatic" value
# class Color
# class Date, DateTime
# class Enum
# class Either
# class Instance
# class Component
# class Array
# class MinMax

__all__ = []
for name, cls in list(globals().items()):
    if isinstance(cls, type) and issubclass(cls, Property):
        __all__.append(name)

del name, cls
