"""
Implements the property decorator, class and desciptor.
"""

from ._loop import loop, this_is_js
from ._action import BaseDescriptor

undefined = None 


class Property(BaseDescriptor):
    """ Base property class. Properties are readonly attributes associated
    with Component classes. Properties can be mutated by actions.
    The ``Property`` class can have any value, the other property classes
    validate/convert the value when it is mutated.
    
    Usage:
    
    .. code-block:: python
        
        class MyComponent(event.Component):
            
            foo = event.Property(7, doc="A property that can be anything")
            bar = event.StringProp(doc='A property that can only be string')
            spam = event.IntProp(8, settable=True)
    
    In the above example, one can see how the initial value can be specified.
    If a omitted, a sensible default value is used. The docstring for the
    property can be provided using the ``doc`` keyword argument. The ``spam``
    property is marked as ``settable``; a ``set_spam()`` action is
    automatically generated.
    
    One can also implement custom properties:

    .. code-block:: python
        
    class MyCustomProp(event.Property):
        ''' A property that can only be 'a', 'b' or 'c'. '''
        
        _default = 'a'
        
        def _validate(self, value):
            if value not in 'abc':
                raise TypeError('MyCustomProp value must be "a", "b" or "c".')
            return value
    
    """
    
    _default = None
    
    def __init__(self, *args, doc='', settable=False):
        # Set initial value
        if len(args) > 1:
            raise TypeError('event.Property() accepts at most 1 positional argument.')
        elif len(args) == 1:
            self._default = args[0]
            if callable(self._default):
                raise TypeError('event.Property() is not a decorator (anymore).')
        # Set doc
        if not isinstance(doc, str):
            raise TypeError('event.Property() doc must be a string.')
        self._doc = doc
        # Set settable
        self._settable = bool(settable)
        
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
        def setter(self, val):
            self._mutate(name, val)
        return setter
    
    def _validate(self, value):
        return value


class AnyProp(Property):
    """ A property that can be anything (like Property). Default None.
    """


class BoolProp(Property):
    """ A property who's values are converted to bool. Default False.
    """
    
    _default = False
    
    def _validate(self, value):
        return bool(value)


class IntProp(Property):
    """ A propery who's values are integers. Floats and strings are converted.
    Default 0.
    """
    
    _default = 0
    
    def _validate(self, value):
        if isinstance(value, (int, float)) or isinstance(value, str):
            return int(value)
        else:
            raise TypeError('%s property cannot accept %s.' %
                            (self.__class__.__name__, value.__class__.__name__))


class FloatProp(Property):
    """ A propery who's values are floats. Integers and strings are converted.
    Default 0.0.
    """
    
    _default = 0.0
    
    def _validate(self, value):
        if isinstance(value, (int, float)) or isinstance(value, str):
            return float(value)
        else:
            raise TypeError('%s property cannot accept %s.' %
                            (self.__class__.__name__, value.__class__.__name__))


class StringProp(Property):
    """ A propery who's values are strings. Default empty string.
    """
    
    _default = ''
    
    def _validate(self, value):
        if not isinstance(value, str):
            raise TypeError('%s property cannot accept %s.' %
                            (self.__class__.__name__, value.__class__.__name__))
        return value


class TupleProp(Property):
    """ A propery who's values are tuples. In JavaScript the values are Array
    objects that have some of their methods disabled. Default empty tuple.
    """
    
    _default = ()
    
    def _validate(self, value):
        if not isinstance(value, (tuple, list)):
            raise TypeError('%s property cannot accept %s.' %
                            (self.__class__.__name__, value.__class__.__name__))
        value = tuple(value)
        if this_is_js():  # pragma: no cover
            # Cripple the object so in-place changes are harder. Note that we
            # cannot prevent setting or deletion of items.
            value.push = undefined
            value.splice = undefined
            value.push = undefined
            value.reverse = undefined
            value.sort = undefined
        return value


class ListProp(Property):
    """ A propery who's values are lists. Default empty list. The value is 
    always copied upon setting, so one can safely provide an initial value.
    """
    
    _default = []
    
    def _validate(self, value):
        if not isinstance(value, (tuple, list)):
            raise TypeError('%s property cannot accept %s.' %
                            (self.__class__.__name__, value.__class__.__name__))
        return list(value)


class ComponentProp(Property):
    """ A propery who's values are Component instances or None. Default None.
    """
    
    _default = None
    
    def _validate(self, value):
        if not (value is None or isinstance(value, Component)):
            raise TypeError('%s property cannot accept %s.' %
                            (self.__class__.__name__, value.__class__.__name__))
        return value


# todo: For more complex stuff, maybe introduce an EitherProp, e.g. String or None.
# EiterProp would be nice, like Bokeh has. Though perhaps its already fine if
# props can be nullable. Note that people can also use AnyProp as a fallback.
# 
# class NullProp(Property):
#     
#     def _validate(self, value):
#         if not value is None:
#             raise TypeError('Null property can only be None.')
# 
# class EitherProp(Property):
#     
#     def __init__(self, *prop_classes, **kwargs):
#         self._sub_classes = prop_classes
#     
#     def _validate(self, value):
#         for cls in self._sub_classes:
#             try:
#                 return cls._validate(self, value)
#             except TypeError:
#                 pass
#             raise TypeError('This %s property cannot accept %s.' %
#                             (self.__class__.__name__, value.__class__.__name__))

# todo: more special properties
# class Auto -> Bokeh has special prop to indicate "automatic" value
# class Color -> I like this, is quite generic
# class Date, DateTime
# class Enum
# class Either
# class Instance
# class Array
# class MinMax


__all__ = []
for name, cls in list(globals().items()):
    if isinstance(cls, type) and issubclass(cls, Property):
        __all__.append(name)

del name, cls

# Delayed import; deal with circular ref
from ._component import Component
