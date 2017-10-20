"""
Implements the emitter decorator, class and desciptor.
"""

from ._action import BaseDescriptor


def emitter(func):
    """ Decorator to turn a Component's method into an emitter.
    
    An emitter makes it easy to emit specific events and functions as a
    placeholder for documenting an event.
    
    .. code-block:: python
    
        class MyObject(event.Component):
           
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
        raise TypeError('The event.emitter() decorator needs a function.')
    if getattr(func, '__self__', None) is not None:  # builtin funcs have __self__
        raise RuntimeError('Invalid use of emitter decorator.')
    return Emitter(func, func.__name__, func.__doc__ or func.__name__)


class Emitter(BaseDescriptor):
    """ Placeholder for documentation and easy emitting of the event.
    """
    
    def __init__(self, func, name, doc):
        self._func = func
        self._name = name
        self._doc = doc
        self.__doc__ = '*emitter*: {}'.format(doc)
    
    def __get__(self, instance, owner):
        if instance is None:
            return self
        
        private_name = '_' + self._name + '_emitter'
        try:
            func = getattr(instance, private_name)
        except AttributeError:
            
            def func(*args):  # this func should return None, so super() works correct
                ev = self._func(instance, *args)
                if ev is not None:
                    instance.emit(self._name, ev)
            func.__doc__ = self.__doc__
            setattr(instance, private_name, func)

        return func
