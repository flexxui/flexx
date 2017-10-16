"""
Implements the property decorator, class and desciptor.
"""

import inspect

from ._loop import loop
from ._action import BaseDescriptor


def prop(default, doc='', setter=None):
    """ Function to define a propery on a Component.
    
    An event is emitted when the property is changed, which has values
    for "old_value" and "new_value".
    
    Usage:
    
    .. code-block:: python
    
        class MyObject(event.Component):
           
            foo = prop(1, setter=int, doc='docstring goes here.')
        
        m = MyObject(foo=2)
        m.set_foo(3)
    
    The first argument is the default value. If ``setter`` is specified,
    the ``set_xxx()`` will be created automatically.
    
    """
    if callable(default):
        raise TypeError('event.prop() is not a decorator (anymore).')
    if not isinstance(doc, str):
        raise TypeError('event.prop() doc must be a string.')
    if not (setter is None or callable(setter)):
        raise TypeError('event.prop() setter must be None or callable.')
    return PropertyDescriptor(default, setter, doc)


def arrayprop(default, setter=None, doc=None):
    raise NotImplementedError()


def readonly(func):
    """ Decorator to define a readonly property. An event is emitted
    when the property is set, which has values for "old_value" and
    "new_value". To set a readonly property internally, use the
    :func:`Component._set_prop() <flexx.event.Component._set_prop>` method.
    
    .. code-block:: python
    
        class MyObject(event.Component):
           
           @readonly
           def bar(self, v=1):
                return float(v)
        
        m = MyObject()
        m._set_prop('bar', 2)  # only for internal use
    
    """
    raise NotImplementedError('Deprecated: use event.prop() instead.')
    # if not callable(func):
    #     raise TypeError('readonly decorator needs a callable')
    # return Readonly(func)


class PropertyDescriptor(BaseDescriptor):
    """ Class descriptor for properties.
    """
    
    def __init__(self, default, setter, doc):
        self._default = default
        self._setter = setter
        self._doc = doc
        self._set_name('anonymous_property')
    
    def _set_name(self, name):
        self._name = name  # or func.__name__
        self.__doc__ = '*property*: %s' % (self._doc or self._name)
                                     
    def __set__(self, instance, value):
        t ='Cannot set property %r; properties can only be mutated by actions.'
        raise AttributeError(t % self._name)
    
    def __get__(self, instance, owner):
        if instance is None:
            return self
        private_name = '_' + self._name + '_value'
        loop.register_prop_access(instance, self._name)
        return getattr(instance, private_name)
