"""
Implements the HasEvents class; the core class via which events are
generated and handled. It is the object that keeps track of handlers.
"""

import sys

from ._dict import Dict
from ._handler import HandlerDescriptor, Handler
from ._emitters import BaseEmitter, Property

def this_is_js():
    return False


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
    * Set the name of each handler and emitter.
    * Sets __handlers__, __emitters, __signals__ attribute on the class.
    """
    
    def __init__(cls, name, bases, dct):
        
        # Collect handlers defined on this class
        handlers = {}
        emitters = {}
        properties = {}
        for name in dir(cls):
            if name.startswith('__'):
                continue
            val = getattr(cls, name)
            if isinstance(val, Property):
                properties[name] = val
            elif isinstance(val, BaseEmitter):
                emitters[name] = val
            elif isinstance(val, HandlerDescriptor):
                handlers[name] = val
            elif name.startswith('on_'):
                val = HandlerDescriptor(val, [name[3:]])
                setattr(cls, name, val)
                handlers[name] = val
        # Finalize all found emitters
        for collection in (handlers, emitters, properties):
            for name, descriptor in collection.items():
                descriptor._name = name
                setattr(cls, '_' + name + '_func', descriptor._func)
        # Cache prop names
        cls.__handlers__ = [name for name in sorted(handlers.keys())]
        cls.__emitters__ = [name for name in sorted(emitters.keys())]
        cls.__properties__ = [name for name in sorted(properties.keys())]
        # Proceed as normal
        type.__init__(cls, name, bases, dct)


class HasEvents(with_metaclass(HasEventsMeta, object)):
    """ Base class for objects that have properties and can emit events.
    Initial values of settable properties can be provided by passing them
    as keyword arguments.
    
    Objects of this class can emit events through their ``emit()``
    method. Subclasses can use the
    :func:`prop <flexx.event.prop>` and :func:`readonly <flexx.event.readonly>`
    decorator to create properties, and the
    :func:`connect <flexx.event.connect>` decorator to create handlers.
    Methods named ``on_foo`` are connected to the event "foo".
    
    .. code-block:: python
    
        class MyObject(event.HasEvents):
            
            # Emitters
            
            @event.prop
            def foo(self, v=0):
                return float(v)
            
            @event.emitter
            def bar(self, v):
                return dict(value=v)  # the event to emit
            
            # Handlers
            
            @event.connect
            def handle_foo(self, *events):
                print('foo was set to', events[-1].new_value)
            
            def on_bar(self, *events):
                print('bar event was generated')
        
        ob = MyObject(foo=42)
        
        @ob.connect('foo')
        def another_foo handler(*events):
            print('foo was set %i times' % len(events))
    
    """
    
    _IS_HASEVENTS = True
    
    def __init__(self, **property_values):
        
        # Init some internal variables
        self._he_handlers = {}
        self._he_props_being_set = {}
        
        # Instantiate handlers, its enough to reference them
        for name in self.__handlers__:
            getattr(self, name)
        # Instantiate emitters
        for name in self.__emitters__:
            self._he_handlers.setdefault(name, [])
        for name in self.__properties__:
            self._he_handlers.setdefault(name, [])
            self._init_prop(name)
        
        # Initialize given properties
        for name, value in property_values.items():
            if name in self.__properties__:
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
        for name, handlers in self._he_handlers.items():
            for label, handler in handlers:
                handler._clear_hasevents_refs(self)
            while len(handlers):
                handlers.pop()  # no list.clear on legacy py
        for name in self.__handlers__:
            getattr(self, name).dispose()
    
    def _register_handler(self, type, handler):
        # Register a handler for the given event type. The type
        # can include a label, e.g. 'mouse_down:foo'.
        # This is called from Handler objects at initialization and when
        # they reconnect (dynamism).
        type, _, label = type.partition(':')
        label = label or handler._name
        handlers = self._he_handlers.setdefault(type, [])
        entry = label, handler
        if entry not in handlers:
            handlers.append(entry)
        handlers.sort(key=lambda x: x[0]+'-'+x[1]._id)
    
    def disconnect(self, type, handler=None):
        """ Disconnect handlers. 
        
        Parameters:
            type (str): the type for which to disconnect any handlers.
                Can include the label to only disconnect handlers that
                were registered with that label.
            handler (optional): the handler object to disconnect. If given,
               only this handler is removed.
        """
        # This is called from Handler objects when they dispose and when
        # they reconnect (dynamism).
        type, _, label = type.partition(':')
        handlers = self._he_handlers.get(type, ())
        for i in reversed(range(len(handlers))):
            entry = handlers[i]
            if not ((label and label != entry[0]) or
                    (handler and handler is not entry[1])):
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
        # Prepare event
        if not isinstance(ev, dict):
            raise TypeError('Event object (for %r) must be a dict' % type)
        ev = Dict(ev)  # make copy and turn into nicer Dict on py
        ev.type = type
        ev.source = self
        # Push the event to the handlers (handlers use labels for dynamism)
        for label, handler in self._he_handlers.get(type, ()):
            handler._add_pending_event(label, ev)  # friend class
    
    def _init_prop(self, prop_name):
        # Initialize a property
        private_name = '_' + prop_name + '_value'
        func_name = '_' + prop_name + '_func'
        # Trigger default value
        func = getattr(self, func_name)
        try:
            value2 = func()
        except Exception as err:
            raise RuntimeError('Could not get default value for property'
                               '%r:\n%s' % (prop_name, err))
        # Update value and emit event
        setattr(self, private_name, value2)
        self.emit(prop_name, dict(new_value=value2, old_value=value2))
    
    def _set_prop(self, prop_name, value):
        """ Set the value of a (readonly) property.
        
        Parameters:
            prop_name (str): the name of the property to set.
            value: the value to set.
        """
        # Checks
        if not isinstance(prop_name, str):
            raise TypeError("_set_prop's first arg must be str, not %s" %
                             prop_name.__class__)
        if prop_name not in self.__properties__:
            cname = self.__class__.__name__
            raise AttributeError('%s object has no property %r' % (cname, prop_name))
        if self._he_props_being_set.get(prop_name, False):
            return
        # Prepare
        private_name = '_' + prop_name + '_value'
        func_name = '_' + prop_name + '_func'
        # Validate value
        self._he_props_being_set[prop_name] = True
        try:
            func = getattr(self, func_name)
            if this_is_js():
                value2 = func.apply(self, [value])
            else:
                value2 = func(value)
        finally:
            self._he_props_being_set[prop_name] = False
        # Update value and emit event
        old = getattr(self, private_name, None)
        if value2 != old:
            setattr(self, private_name, value2)
            self.emit(prop_name, dict(new_value=value2, old_value=old))
    
    def _get_emitter(self, emitter_name):
        # Get an emitter function.
        func_name = '_' + emitter_name + '_func'
        func = getattr(self, func_name)
        def emitter_func(*args):
            if this_is_js():
                ev = func.apply(self, args)
            else:
                ev = func(*args)
            self.emit(emitter_name, ev)
        return emitter_func
    
    def get_event_types(self):
        """ Get the known event types for this HasEvent object. Returns
        a list of event type names, for which there is a
        property/emitter or for which any handlers are registered.
        Sorted alphabetically.
        """
        return list(sorted(self._he_handlers.keys()))
    
    def get_event_handlers(self, type):
        """ Get a list of handlers for the given event type. The order
        is the order in which events are handled: alphabetically by
        label.
        
        Parameters:
            type (str): the type of event to get handlers for. Should not
                include a label.
        
        """
        if not type:
            raise TypeError('get_event_handlers() missing "type" argument.')
        type, _, label = type.partition(':')
        if label:
            raise ValueError('The type given to get_event_handlers() '
                             'should not include a label.')
        handlers = self._he_handlers.get(type, ())
        return [h[1] for h in handlers]

    # This method does *not* get transpiled
    def connect(self, *connection_strings):
        """ Connect a function to one or more events of this instance. Can
        also be used as a decorator. See the
        :func:`connect <flexx.event.connect>` decorator for more information.
        
        .. code-block:: py
            
            h = HasEvents()
            
            # Usage as a decorator
            @h.connect('first_name', 'last_name')
            def greet(*events):
                print('hello %s %s' % (h.first_name, h.last_name))
            
            # Direct usage
            h.connect(greet, 'first_name', 'last_name')
        
        """
        if (not connection_strings) or (len(connection_strings) == 1 and
                                        callable(connection_strings[0])):
            raise RuntimeError('connect() needs one or more connection strings.')
        
        func = None
        if callable(connection_strings[0]):
            func = connection_strings[0]
            connection_strings = connection_strings[1:]
        
        for s in connection_strings:
            if not (isinstance(s, str) and len(s) > 0):
                raise ValueError('Connection string must be nonempty strings.')
        
        def _connect(func):
            if not callable(func):
                raise TypeError('connect() decotator requires a callable.')
            return Handler(func, connection_strings, self)
        
        if func is not None:
            return _connect(func)
        else:
            return _connect
