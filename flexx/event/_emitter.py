"""
Implements the emitter decorator, class and desciptor.
"""

import weakref

from ._action import BaseDescriptor


def emitter(func):
    """ Decorator to turn a method of a Component into an
    :class:`Emitter <flexx.event.Emitter>`.

    An emitter makes it easy to emit specific events, and is also a
    placeholder for documenting an event.

    .. code-block:: python

        class MyObject(event.Component):

           @emitter
           def spam(self, v):
                return dict(value=v)

        m = MyObject()
        m.spam(42)  # emit the spam event

    The method being decorated can have any number of arguments, and
    should return a dictionary that represents the event to generate.
    The method's docstring is used as the emitter's docstring.
    """
    if not callable(func):
        raise TypeError('The event.emitter() decorator needs a function.')
    if getattr(func, '__self__', None) is not None:  # builtin funcs have __self__
        raise TypeError('Invalid use of emitter decorator.')
    return EmitterDescriptor(func, func.__name__, func.__doc__)


class EmitterDescriptor(BaseDescriptor):
    """ Placeholder for documentation and easy emitting of the event.
    """

    def __init__(self, func, name, doc):
        self._func = func
        self._name = name
        self.__doc__ = self._format_doc('emitter', name, doc, func)

    def __get__(self, instance, owner):
        if instance is None:
            return self

        private_name = '_' + self._name + '_emitter'
        try:
            emitter = getattr(instance, private_name)
        except AttributeError:
            emitter = Emitter(instance, self._func, self._name, self.__doc__)
            setattr(instance, private_name, emitter)

        emitter._use_once(self._func)  # make super() work, see _action.py
        return emitter


class Emitter:
    """ Emitter objects are wrappers around Component methods. They take
    care of emitting an event when called and function as a placeholder
    for documenting an event. This class should not be instantiated
    directly; use ``event.emitter()`` instead.
    """

    def __init__(self, ob, func, name, doc):
        assert callable(func)

        # Store func, name, and docstring (e.g. for sphinx docs)
        self._ob1 = weakref.ref(ob)
        self._func = func
        self._func_once = func
        self._name = name
        self.__doc__ = doc

    def __repr__(self):
        cname = self.__class__.__name__
        return '<%s %r at 0x%x>' % (cname, self._name, id(self))

    def _use_once(self, func):
        """ To support super().
        """
        self._func_once = func

    def __call__(self, *args):
        """ Emit the event.
        """
        func = self._func_once
        self._func_once = self._func
        ob = self._ob1()
        if ob is not None:
            ev = func(ob, *args)
            if ev is not None:
                ob.emit(self._name, ev)
