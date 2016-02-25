"""
Implements the HasEvents class; the core class via which events are
generated and handled. It is the object that keeps track of handlers.
"""

import sys

from ._dict import Dict
from ._handler import HandlerDescriptor, Handler
from ._emitters import BaseEmitter


# Reasons to want/need a metaclass:
# * Keep track of subclasses (but can handle that in flexx.app.Model)
# * Wee bit more efficient? (I wonder if it would be measurable)
# * You can turn on_foo() into a handler instead of wrapping it in an
#   internal handler. Though maybe the latter is nicer.
# * If we want to support this, there is no other way:
#   foo = Int(42, 'this is a property')


# todo: delete this?
# # From six.py
# def with_metaclass(meta, *bases):
#     """Create a base class with a metaclass."""
#     # This requires a bit of explanation: the basic idea is to make a dummy
#     # metaclass for one level of class instantiation that replaces itself with
#     # the actual metaclass.
#     # On Python 2.7, the name cannot be unicode :/
#     tmp_name = b'tmp_class' if sys.version_info[0] == 2 else 'tmp_class'
#     class metaclass(meta):
#         def __new__(cls, name, this_bases, d):
#             return meta(name, bases, d)
#     return type.__new__(metaclass, tmp_name, (), {})
# 
# 
# def new_type(name, *args, **kwargs):
#     """ Alternative for type(...) to be legacy-py compatible.
#     """
#     name = name.encode() if sys.version_info[0] == 2 else name
#     return type(name, *args, **kwargs)
# 
#
# class HasEventsMeta(type):
#     """ Meta class for HasEvents
#     * Set the name of each handler
#     * Sets __handlers__ attribute on the class
#     """
#     
#     CLASSES = []
#     
#     def __init__(cls, name, bases, dct):
#         
#         HasEventsMeta.CLASSES.append(cls)
#         
#         # Collect handlers defined on this class
#         handlers = {}
#         emitters = {}
#         for name in dir(cls):
#             if name.startswith('__'):
#                 continue
#             val = getattr(cls, name)
#             if isinstance(val, BaseEmitter):
#                 emitters[name] = val
#             elif isinstance(val, HandlerDescriptor):
#                 handlers[name] = val
#             elif name.startswith('on_'):
#                 val = HandlerDescriptor(val, [name[3:]],  sys._getframe(1))
#                 setattr(cls, name, val)
#                 handlers[name] = val
#         # Finalize all found emitters
#         for name, emitter in emitters.items():
#             emitter._name = name
#         for name, handler in handlers.items():
#             handler._name = name
#         # Cache prop names
#         cls.__handlers__ = [name for name in sorted(handlers.keys())]
#         cls.__emitters__ = [name for name in sorted(emitters.keys())]
#         # Proceed as normal
#         type.__init__(cls, name, bases, dct)


#class HasEvents(with_metaclass(HasEventsMeta, object)):
class HasEvents:
    """ Base class for objects that have event emitters and or properties.
    
    Objects of this class can emit events through their ``emit()``
    method. Handlers can connect to these objects (and they keep
    references to the handlers).
    
    Dedicated handlers can be created by creating methods starting with 'on_'.
    
    Initial values of settable properties can be provided by passing them
    as keyword arguments.
    
    
    Example use:
    
    .. code-block:: python
    
        class MyObject(event.HasEvents):
            
            # Emitters
            
            @event.prop
            def foo(self, v=0):
                return float(v)
            
            event.emitter
            def bar(self, v):
                return dict(value=v)  # the event to emit
            
            # Handlers
            
            @event.connect
            def handle_foo(self, *events):
                print('foo was set to', events[-1].new_value)
            
            def on_bar(self, *events):
                print('bar event was generated')
        
        ob = MyObject(foo=42)
        
        @event.connect('foo')
        def another_foo handler(*events):
            print('foo was set %i times' % len(events))
    
    """
    
    _IS_HASEVENTS = True
    
    def __init__(self, **initial_property_values):
        self._handlers = {}
        
        # Detect our emitters and handlers
        handlers, emitters = {}, {}
        for name in dir(self.__class__):
            if name.startswith('__'):
                continue
            val = getattr(self.__class__, name)
            if isinstance(val, BaseEmitter):
                emitters[name] = val
            elif isinstance(val, HandlerDescriptor):
                handlers[name] = val
            elif name.startswith('on_') and callable(val):
                hh = self._handlers.setdefault(name[3:], [])
                # todo: pass a dummy frame, otherwise this __init__ gets stuck?
                Handler(val,[name[3:]], None, self)  # registers itself
        
        self.__handlers__ = [name for name in sorted(handlers.keys())]
        self.__emitters__ = [name for name in sorted(emitters.keys())]
        
        # Instantiate handlers, its enough to reference them
        for name in self.__handlers__:
            getattr(self, name)
        # Instantiate emitters
        for name in self.__emitters__:
            getattr(self, name)  # trigger setting the default value for props
            self._handlers.setdefault(name, [])
        
        # Initialize given properties
        for name, value in initial_property_values.items():
            if name in self.__emitters__:
                setattr(self, name, value)
            else:
                cname = self.__class__.__name__
                raise AttributeError('%s does not have a property %r' % (cname, name))
    
    def dispose(self):
        """ Use this to dispose of the object to prevent memory leaks.
        
        Make all subscribed handlers to forget about this object, clear
        all references to subscribed handlers, disconnect all handlers
        defined on this object.
        """
        for name, handlers in self._handlers.items():
            for label, handler in handlers:
                handler._clear_hasevents_refs(self)
            handlers[:] = []
        for name in self.__handlers__:
            getattr(self, name).disconnect(destroy)
    
    def _register_handler(self, type, handler):
        # todo: include connection_string?
        """ Register a handler for the given event type. The type
        can include a label, e.g. 'mouse_down:foo'.
        This is called from Handler objects at initialization and when
        they reconnect (dynamism).
        """
        type, _, label = type.partition(':')
        label = label or handler.name
        handlers = self._handlers.setdefault(type, [])
        entry = label, handler
        if entry not in handlers:
            handlers.append(entry)
        handlers.sort(key=lambda x: x[0]+'-'+x[1]._id)
    
    def _unregister_handler(self, type, handler=None):
        """ Unregister a handler. This is called from Handler objects
        when they dispose or when they reconnect (dynamism).
        """
        type, _, label = type.partition(':')
        handlers = self._handlers.get(type, ())
        topop = []
        for i, entry in enumerate(handlers):
            if not ((label and label != entry[0]) or
                    (handler and handler is not entry[1])):
                topop.append(i)
        for i in reversed(topop):
            handlers.pop(i)
    
    def emit(self, type, ev):
        """ Generate a new event and dispatch to all event handlers.
        
        Arguments:
            type (str): the type of the event. Should not include a label.
            ev (dict): the event object. This dict is turned into a Dict,
                so that its elements can be accesses as attributes.
        """
        type, _, label = type.partition(':')
        if label:
            raise ValueError('The type given to emit() should not include a label.')
        if not isinstance(ev, dict):
            raise TypeError('Event object (for %r) must be a dict' % type)
        for label, handler in self._handlers.get(type, ()):
            ev = Dict(ev)
            ev.type = type
            ev.label = label
            ev.source = self
            handler._add_pending_event(ev)  # friend class
    
    def _set_prop(self, prop_name, value):
        """ Set the value of a (readonly) property.
        
        Parameters:
            prop_name (str): the name of the property to set.
            value: the value to set.
        """
        if not isinstance(prop_name, str):
            raise ValueError("_set_prop's first arg must be str, not %s" %
                             prop_name.__class__.__name__)
        try:
            readonly_descriptor = getattr(self.__class__, prop_name)
        except AttributeError:
            cname = self.__class__.__name__
            raise AttributeError('%s object has no property %r' % (cname, prop_name))
        readonly_descriptor._set(self, value)
    
    def get_event_types(self):
        """ Get the known event types for this HasEvent object.
        
        Returns:
            types (list): a list of event type names, for which there
            is a property/emitter or for which any handlers are
            registered. Sorted alphabetically.
        """
        return list(sorted(self._handlers.keys()))
    
    def get_event_handlers(self, type):
        """ Get a list of handlers for the given event type.
        
        Parameters:
            type (str): the type of event to get handlers for. Should not
                include a label.
        
        Returns:
            handlers (list): a list of handler objects. The order is
            the order in which events are handled: alphabetically by
            label.
        """
        type, _, label = type.partition(':')
        if label:
            raise ValueError('The type given to get_event_handlers() should not include a label.')
        handlers = self._handlers.get(type, ())
        return [h[1] for h in handlers]
