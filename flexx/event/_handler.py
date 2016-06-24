"""
Implementation of handler class and corresponding descriptor.
"""

import sys
import inspect
import weakref

from ._dict import Dict
from ._loop import loop
from . import logger


def this_is_js():
    return False

console = setTimeout = None


# Decorator to wrap a function in a Handler object
def connect(*connection_strings):
    """ Decorator to turn a method of HasEvents into an event
    :class:`Handler <flexx.event.Handler>`.
    
    A method can be connected to multiple event types. Each connection
    string represents an event type to connect to. Read more about
    dynamism and labels for further information on the possibilities
    of connection strings.
    
    To connect functions or methods to an event from another HasEvents
    object, use that object's
    :func:`HasEvents.connect()<flexx.event.HasEvents.connect>` method.
    
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
        t = '<%s %r(this should be a class attribute) at 0x%x>'
        return t % (self.__class__.__name__, self._name, id(self))
        
    def __set__(self, obj, value):
        raise AttributeError('Cannot overwrite handler %r.' % self._name)
    
    def __delete__(self, obj):
        raise AttributeError('Cannot delete handler %r.' % self._name)
    
    def __get__(self, instance, owner):
        if instance is None:
            return self
        
        private_name = '_' + self._name + '_handler'
        try:
            handler = getattr(instance, private_name)
        except AttributeError:
            handler = Handler(self._func, self._connection_strings, instance)
            setattr(instance, private_name, handler)
        
        # Make the handler use *our* func one time. In most situations
        # this is the same function that the handler has, but not when
        # using super(); i.e. this allows a handler to call the same
        # handler of its super class.
        handler._use_once(self._func)
        return handler
    
    @property
    def local_connection_strings(self):
        """ List of connection strings that are local to the object.
        """
        return [s for s in self._connection_strings if '.' not in s]


class Handler:
    """ Wrapper around a function object to connect it to one or more events.
    This class should not be instantiated directly; use ``event.connect`` or
    ``HasEvents.connect`` instead.
    
    Arguments:
        func (callable): function that handles the events.
        connection_strings (list): the strings that represent the connections.
        ob (HasEvents): the HasEvents object to use a a basis for the
            connection. A weak reference to this object is stored. It
            is passed a a first argument to the function in case its
            first arg is self.
    """
    
    _count = 0
    
    def __init__(self, func, connection_strings, ob):
        # Check and set func
        assert callable(func)
        self._func = func
        self._func_once = func
        self._name = func.__name__
        Handler._count += 1
        self._id = 'h%i' % Handler._count  # to ensure a consistent event order
        
        # Set docstring; this appears correct in sphinx docs
        self.__doc__ = '*%s*: %s' % ('event handler', func.__doc__ or self._name)
        
        # Store object using a weakref
        self._ob = weakref.ref(ob)
        
        # Get whether function is a method
        try:
            self._func_is_method = inspect.getargspec(func)[0][0] in ('self', 'this')
        except (TypeError, IndexError):
            self._func_is_method = False
        if getattr(func, '__self__', None) is not None:
            self._func_is_method = False  # already bound
        
        self._init(connection_strings)
    
    
    def _init(self, connection_strings):
        """ Init of this handler that is compatible with PyScript.
        """
        # Init connections
        self._connections = []
        for s in connection_strings:
            d = Dict()  # don't do Dict(foo=x) bc PyScript only supports that for dict
            self._connections.append(d)
            d.fullname = s
            d.type = s.split('.')[-1]
            d.objects = []
        
        # Pending events for this handler
        self._scheduled_update = False
        self._pending = []  # pending events
        
        # Connect
        for index in range(len(self._connections)):
            self._connect_to_event(index)
    
    def __repr__(self):
        c = '+'.join([str(len(c.objects)) for c in self._connections])
        cname = self.__class__.__name__
        return '<%s %r with %s connections at 0x%x>' % (cname, self._name, c, id(self))
    
    def get_name(self):
        """ Get the name of this handler, usually corresponding to the name
        of the function that this handler wraps.
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
    
    def _use_once(self, func):
        self._func_once = func
    
    def __call__(self, *events):
        """ Call the handler function.
        """
        func = self._func_once
        if self._func_is_method and self._ob is not None:
            res = func(self._ob(), *events)
        else:
            res = func(*events)
        self._func_once = self._func
        return res
    
    def _add_pending_event(self, label, ev):
        """ Add an event object to be handled at the next event loop
        iteration. Called from HasEvents.emit().
        """
        if not self._scheduled_update:
            # register only once
            self._scheduled_update = True
            if this_is_js():
                setTimeout(self._handle_now_callback.bind(self), 0)
            else:
                loop.call_later(self._handle_now_callback)
        self._pending.append((label, ev))
    
    def _handle_now_callback(self):
        self._scheduled_update = False
        self.handle_now()
    
    def handle_now(self):
        """ Invoke a call to the handler function with all pending
        events. This is normally called in a next event loop iteration
        when an event is scheduled for this handler, but it can also
        be called manually to force the handler to process pending
        events *now*.
        """
        # Collect pending events and check what connections need to reconnect
        events = []
        reconnect = []
        for label, ev in self._pending:
            if label.startswith('reconnect_'):
                index = int(label.split('_')[-1])
                reconnect.append(index)
            else:
                events.append(ev)
        self._pending = []
        # Reconnect (dynamism)
        for index in reconnect:
            self._connect_to_event(index)
        # Handle events
        if len(events):
            if not this_is_js():
                logger.debug('Handler %s is processing %i events' %
                            (self._name, len(events)))
            try:
                self(*events)
            except Exception as err:
                if this_is_js():
                    console.log(err)
                else:
                    # Allow post-mortem debugging
                    type_, value, tb = sys.exc_info()
                    tb = tb.tb_next  # Skip *this* frame
                    sys.last_type = type_
                    sys.last_value = value
                    sys.last_traceback = tb
                    tb = None  # Get rid of it in this namespace
                    # Show the exception
                    logger.exception(value)
    
    
    ## Connecting
    
    def dispose(self):
        """ Cleanup any references.
        
        Disconnects all connections, and cancel all pending events.
        """
        if not this_is_js():
            logger.debug('Disposing Handler %r ' % self)
        for connection in self._connections:
            while len(connection.objects):
                ob, name = connection.objects.pop(0)
                ob.disconnect(name, self)
        while len(self._pending):
            self._pending.pop()  # no list.clear on legacy py
    
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
        """ Seek an event object based on the name (PyScript compatible).
        """
        connection = self._connections[index]
        
        # Done traversing name: add to list or fail
        if ob is None or not len(path):
            if ob is None or not hasattr(ob, '_IS_HASEVENTS'):
                return  # we cannot seek further
            connection.objects.append((ob, connection.type))
            return  # found it
        
        # Resolve name
        obname, path = path[0], path[1:]
        if hasattr(ob, '_IS_HASEVENTS') and obname in ob.__properties__:
            name_label = obname + ':reconnect_' + str(index)
            connection.objects.append((ob, name_label))
            ob = getattr(ob, obname, None)
        elif obname == '*' and isinstance(ob, (tuple, list)):
            for sub_ob in ob:
                self._seek_event_object(index, path, sub_ob)
            return
        else:
            ob = getattr(ob, obname, None)
        return self._seek_event_object(index, path, ob)
