"""
Implements the attribute class.
"""

from ._action import BaseDescriptor


# todo: fix docs below
class Attribute(BaseDescriptor):
    """ Attributes are (readonly) attributes associated
    with Component classes. Properties can be mutated by actions.
    The ``Property`` class can have any value, the other property classes
    validate/convert the value when it is mutated.
    
    Usage:
    
    .. code-block:: python
        
        class MyComponent(event.Component):
            
            foo = event.Property(7, doc="A property that can be anything")
            bar = event.StringProp(doc='A property that can only be string')
            spam = event.IntProp(8, settable=True)
    
    In the example above, one can see how the initial value can be specified.
    If omitted, a sensible default value is used. The docstring for the
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
    
    def __init__(self, doc=''):
        # Set doc
        if not isinstance(doc, str):
            raise TypeError('event.Attribute() doc must be a string.')
        self._doc = doc
        self._set_name('anonymous_attribute')
    
    def _set_name(self, name):
        self._name = name  # or func.__name__
        self.__doc__ = '*attribute*: %s' % (self._doc or self._name)
                                     
    def __set__(self, instance, value):
        t = 'Cannot set attribute %r.'
        raise AttributeError(t % self._name)
    
    def __get__(self, instance, owner):
        if instance is None:
            return self
        return getattr(instance, '_' + self._name)
