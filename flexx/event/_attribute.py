"""
Implements the attribute class.
"""

from ._action import BaseDescriptor


class Attribute(BaseDescriptor):
    """ Attributes are (readonly, and usually static) values associated with
    Component classes. They expose and document a value without
    providing means of observing changes like ``Property`` does. (The
    actual value is taken from ``component._xx``, with "xx" the name
    of the attribute.)

    """

    def __init__(self, doc=''):
        # Set doc
        if not isinstance(doc, str):
            raise TypeError('event.Attribute() doc must be a string.')
        self._doc = doc
        self._set_name('anonymous_attribute')

    def _set_name(self, name):
        self._name = name  # or func.__name__
        self.__doc__ = self._format_doc('attribute', name, self._doc)

    def __set__(self, instance, value):
        t = 'Cannot set attribute %r.'
        raise AttributeError(t % self._name)

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return getattr(instance, '_' + self._name)
