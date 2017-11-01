"""
Implements the action decorator, class and desciptor.
"""

import weakref

from ._loop import loop
from . import logger


def action(func):
    """ Decorator to turn a method of a Component into an
    :class:`Action <flexx.event.Action>`.
    
    Actions change the state of the application by mutating properties.
    In fact, properties can only be changed via actions.
    
    Actions are asynchronous and thread-safe. Invoking an action will not
    apply the changes directly; the action is queued and handled at a later
    time. The one exception is that when an action is invoked from anoher
    action, it is handled directly.
    
    Although setting properties directly might seem nice, their use would mean
    that the state of the application can change while the app is *reacting*
    to changes in the state. This might be managable for small applications,
    but as an app grows this easily results in inconsistencies and bugs.
    Separating actions (which modify state) and reactions (that react to it)
    makes apps easier to understand and debug. This is the core idea behind
    frameworks such as Elm, React and Veux. And Flexx adopts it as well.
    
    Usage:
    
    .. code-block:: py
        
        class MyComponent(event.Component):
            
            count = event.IntProp(0)
            
            @action
            def increase_counter(self):
                self._mutate_count(self.count + 1)  # call mutator function
    
    """
    if not callable(func):
        raise TypeError('The event.action() decorator needs a function.')
    if getattr(func, '__self__', None) is not None:  # builtin funcs have __self__
        raise TypeError('Invalid use of action decorator.')
    return ActionDescriptor(func, func.__name__, func.__doc__ or func.__name__)


class BaseDescriptor:
    """ Base descriptor class for some commonalities.
    """
    
    def __repr__(self):
        t = '<%s %r (this should be a class attribute) at 0x%x>'
        return t % (self.__class__.__name__, self._name, id(self))

    def __set__(self, obj, value):
        cname = self.__class__.__name__
        cname = cname[:-10] if cname.endswith('Descriptor') else cname
        raise AttributeError('Cannot overwrite %s %r.' % (cname, self._name))

    def __delete__(self, obj):
        cname = self.__class__.__name__
        cname = cname[:-10] if cname.endswith('Descriptor') else cname
        raise AttributeError('Cannot delete %s %r.' % (cname, self._name))


class ActionDescriptor(BaseDescriptor):
    """ Class descriptor for actions.
    """

    def __init__(self, func, name, doc):
        self._func = func
        self._name = name
        self._doc = doc
        self.__doc__ = '*action*: {}'.format(doc)

    def __get__(self, instance, owner):
        # Return Action object, which we cache on the instance
        if instance is None:
            return self

        private_name = '_' + self._name + '_action'
        try:
            action = getattr(instance, private_name)
        except AttributeError:
            action = Action(instance, self._func, self._name, self._doc)
            setattr(instance, private_name, action)

        # Make the action use *our* func one time. In most situations
        # this is the same function that the action has, but not when
        # using super(); i.e. this allows an action to call the same
        # action of its super class.
        action._use_once(self._func)
        return action
    

class Action:
    """ Action objects are wrappers around Component methods. They take
    care of queueing action invokations rather than calling the function
    directly, unless the action is called from another action (in this
    case it would a direct call). This class should not be instantiated
    directly; use ``event.action()`` instead.
    """
    
    def __init__(self, ob, func, name, doc):
        assert callable(func)
        
        # Store func, name, and docstring (e.g. for sphinx docs)
        self._ob1 = weakref.ref(ob)
        self._func = func
        self._func_once = func
        self._name = name
        self.__doc__ = '*action*: {}'.format(doc)
    
    def __repr__(self):
        cname = self.__class__.__name__
        return '<%s %r at 0x%x>' % (cname, self._name, id(self))

    def _use_once(self, func):
        """ To support super().
        """
        self._func_once = func

    def __call__(self, *args):
        """ Invoke the action.
        """
        if loop.is_processing_actions():
            func = self._func_once
            self._func_once = self._func
            ob = self._ob1()
            if ob is not None:
                res = func(ob, *args)
                if res is not None:
                    logger.warn('Action (%s) is not supposed to return a value' %
                                self._name)
        else:
            loop.add_action_invokation(self, args)
        
        return None  # 'Actions are invoked asynchronously'
