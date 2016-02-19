import sys

from ._dict import Dict
from ._handler import HandlerDescriptor, Handler
from ._properties import Property

# From six.py
def with_metaclass(meta, *bases):
    """Create a base class with a metaclass."""
    # This requires a bit of explanation: the basic idea is to make a dummy
    # metaclass for one level of class instantiation that replaces itself with
    # the actual metaclass.
    # On Python 2.7, the name cannot be unicode :/
    tmp_name = b'tmp_class' if sys.version_info[0] == 2 else 'tmp_class'
    class metaclass(meta):
        def __new__(cls, name, this_bases, d):
            return meta(name, bases, d)
    return type.__new__(metaclass, tmp_name, (), {})


def new_type(name, *args, **kwargs):
    """ Alternative for type(...) to be legacy-py compatible.
    """
    name = name.encode() if sys.version_info[0] == 2 else name
    return type(name, *args, **kwargs)


class HasEventsMeta(type):
    """ Meta class for HasEvents
    * Set the name of each handler
    * Sets __handlers__ attribute on the class
    """
    
    CLASSES = []
    
    def __init__(cls, name, bases, dct):
        
        HasEventsMeta.CLASSES.append(cls)  # todo: dict by full qualified name?
        
        
        # Collect handlers defined on this class
        handlers = {}
        props = {}
        for name in dir(cls):
            if name.startswith('__'):
                continue
            val = getattr(cls, name)
            # if isinstance(val, type) and issubclass(val, Signal):
            #     val = val()
            #     setattr(cls, name, val)  # allow setting just class
            if isinstance(val, Property):
                props[name] = val
            elif isinstance(val, HandlerDescriptor):
                handlers[name] = val
            elif name.startswith('on_'):
                val = HandlerDescriptor(val, [name[3:]],  sys._getframe(1))
                setattr(cls, name, val)
                handlers[name] = val
        # Finalize all found props
        for name, prop in props.items():
            prop._name = name
        for name, handler in handlers.items():
            handler._name = name
        # Cache prop names
        cls.__handlers__ = [name for name in sorted(handlers.keys())]
        cls.__props__ = [name for name in sorted(props.keys())]
        # Proceeed as normal
        type.__init__(cls, name, bases, dct)


class HasEvents(with_metaclass(HasEventsMeta, object)):
    """ Base class for objects that have events and/or properties.
    """
    
    _IS_HASSIGNALS = True
    
    def __init__(self, **initial_property_values):
        self._handlers = {}
        self._handlers_reconnect = {}  # handlers to reconnect upon event
        
        # Instantiate handlers, its enough to reference them
        for name in self.__class__.__handlers__:
            getattr(self, name)
        # Instantiate props
        for name in self.__class__.__props__:
            getattr(self, name)  # triggers setting default value
        for name, value in initial_property_values.items():
            if name in self.__class__.__props__:
                setattr(self, name, value)
            
        
        # self._connect_handlers(False)
        
        # for name, val in initial_property_values.items():
        #     if name not in self.__class__.__signals__:
        #         raise ValueError('Object does not have a signal %r' % name)
        #     signal = getattr(self, name)
        #     signal(val)
    
    # def _connect_handlers(self, raise_on_fail=True):
    #     """ Connect any disconnected handler associated with this object.
    #     """
    #     # todo: do we need this public?
    #     success = True
    #     for name in self.__class__.__handlers__:
    #         handler = getattr(self, name)
    #         if handler.not_connected:
    #             connected = handler.connect(raise_on_fail)  # dont combine this with next line
    #             success = success and connected
    #     return success
    
    # todo: rename destroy() or dispose()?
    def disconnect_handlers(self, destroy=True):
        """ Disconnect all subscribed handlers, and all handlers defined
        on this object. This can be used to clean up any references
        when the object is no longer used.
        """
        for name, handlers in self._handlers_reconnect.items():
            handlers[:] = []
        for name, handlers in self._handlers.items():
            handlers[:] = []
        for name in self.__class__.__handlers__:
            getattr(self, name).disconnect(destroy)
    
    # todo: rename connect?
    def _register_handler(self, event_name, handler):
        """ Register a handler for the given event name.
        This is called from Handler objects at initialization and when
        they reconnect (dynamism).
        """
        event_name, _, label = event_name.partition(':')
        label = label or handler._name
        handlers = self._handlers.setdefault(event_name, [])
        entry = label, handler
        if entry not in handlers:
            handlers.append(entry)
        handlers.sort(key=lambda x: x[0]+'-'+x[1]._id)
    
    def _register_handler_reconnect(self, event_name, handler):
        """ Register that the given handler is reconnected when the
        given event occurs. This is called from Handler objects.
        """
        event_name, _, label = event_name.partition(':')
        handlers = self._handlers_reconnect.setdefault(event_name, [])
        entry = label, handler
        if entry not in handlers:
            handlers.append(entry)
        handlers.sort(key=lambda x: x[0]+'-'+x[1]._id)
    
    def _unregister_handler(self, event_name, handler):
        """ Unregister a handler. This is called from Handler objects
        when they dispose or when they reconnect (dynamism).
        """
        handlers = self._handlers_reconnect.setdefault(event_name, [])
        topop = []
        for i, entry in enumerate(handlers):
            if handler in entry:
                topop.append(i)
        for i in reversed(topop):
            handlers.pop(i)
        
        handlers = self._handlers.setdefault(event_name, [])
        topop = []
        for i, entry in enumerate(handlers):
            if handler in entry:
                topop.append(i)
        for i in reversed(topop):
            handlers.pop(i)
    
    def emit(self, event_name, ev):
        """ Generate a new event and dispatch to all event handlers.
        
        Arguments:
            name (str): the name of the event.
            ev (dict): the event object. This dict is turned into a Dict,
                so that its elements can be accesses as attributes.
        """
        # Normalize dict
        if not isinstance(ev, dict):
            raise ValueError('Event object must be a dict')
        ev = Dict(ev)
        ev.type = event_name
        # Dispatch reconnect handlers
        for label, handler in self._handlers_reconnect.get(event_name, ()):
            ev.label = label
            handler.add_pending_event(ev, True)
        # Dispatch registered handlers
        for label, handler in self._handlers.get(event_name, ()):
            ev.label = label
            handler.add_pending_event(ev)
