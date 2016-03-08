import sys
import logging
import inspect
import weakref

from ._dict import Dict
from ._emitters import Property

# todo: define better, or don't use at all?
undefined = 'blaaaaa'


# todo: Silly event loop

class EventLoop:
    def __init__(self):
        self._pending_calls = []
        
    def call_later(self, func):
        self._pending_calls.append(func)
    
    def iter(self):
        while self._pending_calls:
            func = self._pending_calls.pop(0)
            func()
    
    def __enter__(self):
        return self
    
    def __exit__(self, type, value, traceback):
        self.iter()

loop = EventLoop()


# Decorator to wrap a function in a Handler object
def connect(*connection_strings):
    """ Decorator to connect a handler to one or more events.
    
    Example:
        
        .. code-block:: py
            
            class MyObject(event.HasEvents):
                @event.connect('first_name', 'last_name')
                def greet(self, *events):
                    print('hello %s %s' % (self.first_name, self.last_name))
    """
    if (not connection_strings) or (len(connection_strings) == 1 and
                                    callable(connection_strings[0])):
        raise RuntimeError('Connect decorator needs one or more event strings.')
    
    func = None
    if callable(connection_strings[0]):
        func = connection_strings[0]
        connection_strings = connection_strings[1:]
    
    for s in connection_strings:
        if not (isinstance(s, str) and len(s) > 0):
            raise ValueError('Connection string must be nonempty strings.')
    
    def _connect(func):
        if not callable(func):
            raise TypeError('connect() decorator requires a callable.')
        return HandlerDescriptor(func, connection_strings)
    
    if func is not None:
        return _connect(func)
    else:
        return _connect


class HandlerDescriptor:
    """ Class descriptor for handlers.
    """
    
    def __init__(self, func, connection_strings):
        assert callable(func)  # HandlerDescriptor is not instantiated directly
        self._func = func
        self._name = func.__name__  # updated by HasEvents meta class
        self._connection_strings = connection_strings
        self.__doc__ = '*%s*: %s' % ('event handler', func.__doc__ or self._name)
    
    def __repr__(self):
        cls_name = self.__class__.__name__
        return '<%s (this should be a class attribute) at 0x%x>' % (cls_name, id(self))
        
    def __set__(self, obj, value):
        raise AttributeError('Cannot overwrite handler %r.' % self._name)
    
    def __delete__(self, obj):
        raise AttributeError('Cannot delete handler %r.' % self._name)
    
    def __get__(self, instance, owner):
        if instance is None:
            return self
        
        private_name = '_' + self._name + '_handler'
        try:
            return getattr(instance, private_name)
        except AttributeError:
            new = Handler(self._func, self._connection_strings, instance)
            setattr(instance, private_name, new)
            return new


class Handler:
    """ Wrapper around a function object to connect it to one or more events.
    This class should not be instantiated directly; use the decorators instead.
    
    Arguments:
        func (callable): function that handles the events.
        connection_strings (list): the strings that represent the connections.
        ob (HasEvents): the HasEvents object to use a a basis for the
            connection. A weak reference to this object is stored. It
            is passed a a first argument to the function in case its
            first arg is self.
    """
    # todo: need any of this?
    _IS_HANDLER = True  # poor man's isinstance in JS (because class name mangling)
    _count = 0
    
    def __init__(self, func, connection_strings, ob):
        # Check and set func
        assert callable(func)
        self._func = func
        self._name = func.__name__
        Handler._count += 1
        self._id = str(Handler._count)  # to ensure a consistent event order
        
        # Set docstring; this appears correct in sphinx docs
        self.__doc__ = '*%s*: %s' % ('event handler', func.__doc__ or self._name)
        
        # Init connections
        self._connections = [Dict(fullname=s, type=s.split('.')[-1], objects=[])
                             for s in connection_strings]
        
        # Pending events for this handler
        self._scheduled_update = False
        self._pending = []  # pending events
        
        # Store object using a weakref
        self._ob = weakref.ref(ob)
        
        # Get whether function is a method
        try:
            self._func_is_method = inspect.getargspec(func)[0][0] in ('self', 'this')
        except (TypeError, IndexError):
            self._func_is_method = False
        
        # Connect
        for index in range(len(self._connections)):
            self._connect_to_event(index)
    
    def __repr__(self):
        conn = '+'.join([str(len(c.objects)) for c in self._connections])
        cls_name = self.__class__.__name__
        return '<%s %r with %s connections at 0x%x>' % (cls_name, self._name, conn, id(self))
    
    def get_name(self):
        """ Get the name of this handler, usually corresponding to the name
        of the function that this signal wraps.
        """
        return self._name
    
    def get_connection_info(self):
        """ Get a list of tuples (name, connection_names), where
        connection_names is a list of type names (including label) for
        the made connections.
        """
        return [(c.fullname, [u[1] for u in c.objects])
                for c in self._connections]
    
    ## Calling / handling
    
    def __call__(self):
        """ Call the handler function.
        """
        if self._func_is_method and self._ob is not None:
            return self._func(self._ob())
        else:
            return self._func()
    
    def _add_pending_event(self, label, ev):
        """ Add an event object to be handled at the next event loop
        iteration. Called from HasEvents.emit().
        """
        if not self._scheduled_update:
            self._scheduled_update = True
            loop.call_later(self.handle_now)  # register only once
        self._pending.append((label, ev))
    
    def handle_now(self):
        """ Invoke a call to the handler function with all pending
        events. This is normally called in a next event loop iteration
        when an event is scheduled for this handler, but it can also
        be called manually to force the handler to process pending
        events *now*.
        """
        self._scheduled_update = False
        # Collect pending events and check what connections need to reconnect
        events = []
        reconnect = []
        for label, ev in self._pending:
            events.append(ev)
            if label.startswith('reconnect_'):
                index = int(label.split('_')[-1])
                reconnect.append(index)
        self._pending = []
        # Reconnect (dynamism)
        for index in reconnect:
            self._connect_to_event(index)
        # Handle events
        if events:
            try:
                if self._func_is_method and self._ob is not None:
                    return self._func(self._ob(), *events)
                else:
                    return self._func(*events)
            except Exception:
                # Allow post-mortem debugging
                type_, value, tb = sys.exc_info()
                tb = tb.tb_next  # Skip *this* frame
                sys.last_type = type_
                sys.last_value = value
                sys.last_traceback = tb
                del tb  # Get rid of it in this namespace
                # Show the exception
                logging.exception(value)
    
    
    ## Connecting
    
    def dispose(self):
        """ Cleanup any references.
        
        Disconnects all connections, and cancel all pending events.
        """
        for connection in self._connections:
            while len(connection.objects):
                ob, name = connection.objects.pop(0)
                ob.disconnect(name, self)
        self._pending[:] = []
    
    def _clear_hasevents_refs(self, ob):
        """ Clear all references to the given HasEvents instance. This is
        called from a HasEvents' dispose() method. This handler remains
        working, but wont receive events from that object anymore.
        """
        for connection in self._connections:
            for i in reversed(range(len(connection.objects))):
                if connection.objects[i][0] is ob:
                    connection.objects.pop(i)
        
        # Do not clear pending events. This handler is assumed to continue
        # working, and should thus handle its pending events at some point,
        # at which point it cannot hold any references to ob anymore.
    
    def _connect_to_event(self, index):
        """ Connect one connection.
        """
        connection = self._connections[index]
        
        # Disconnect
        while len(connection.objects):
            ob, name = connection.objects.pop(0)
            ob.disconnect(name, self)
        
        path = connection.fullname.split('.')[:-1]
        
        # Obtain root object and setup connections
        ob = self._ob()
        if ob is not None:
            self._seek_event_object(index, path, ob)
        
        # Verify
        if not connection.objects:
            raise RuntimeError('Could not connect to %r' % connection.fullname)
        
        # Connect
        for ob, type in connection.objects:
            ob._register_handler(type, self)
    
    def _seek_event_object(self, index, path, ob):
        """ Seek an event object based on the name.
        This bit is PyScript compatible (_resolve_signals is not).
        """
        connection = self._connections[index]
        
        # Done traversing name: add to list or fail
        if ob is undefined or len(path) == 0:
            if ob is undefined or not hasattr(ob, '_IS_HASEVENTS'):
                return  # we cannot seek further
            connection.objects.append((ob, connection.type))
            return  # found it
        
        # Resolve name
        obname, path = path[0], path[1:]
        if getattr(getattr(ob.__class__, obname, None), '_IS_PROP', False):
            # todo: make .__class__ work in PyScript
            name_label = obname + ':reconnect_' + str(index)
            connection.objects.append((ob, name_label))
            ob = getattr(ob, obname)
        elif obname == '*' and isinstance(ob, (tuple, list)):
            for sub_ob in ob:
                msg = self._seek_event_object(index, path, sub_ob)
                if msg:
                    return msg
            return
        else:
            ob = getattr(ob, obname, undefined)
        return self._seek_event_object(index, path, ob)
