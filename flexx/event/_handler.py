"""
Implementation of handler class and corresponding descriptor.
"""

import weakref
import inspect

from ._dict import Dict
from ._loop import loop
from . import logger


window = None
console = logger


def this_is_js():
    return False


def looks_like_method(func):
    if hasattr(func, '__func__'):
        return False  # this is a bound method
    try:
        return inspect.getargspec(func)[0][0] in ('self', 'this')
    except (TypeError, IndexError):
        return False


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
        if not looks_like_method(func):
            raise TypeError('connect() decorator requires a method '
                            '(first arg must be self).')
        return HandlerDescriptor(func, connection_strings)

    if func is not None:
        return _connect(func)
    else:
        return _connect


class HandlerDescriptor:
    """ Class descriptor for handlers.

    Arguments:
        func (callable): function that handles the events.
        connection_strings (list): the strings that represent the connections.
        ob (HasEvents, optional): the HasEvents object to use a a basis for the
            connection. A weak reference to this object is stored.
    """

    def __init__(self, func, connection_strings, ob=None):
        assert callable(func)  # HandlerDescriptor is not instantiated directly
        self._func = func
        self._name = func.__name__  # updated by HasEvents meta class
        self._ob = None if ob is None else weakref.ref(ob)
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
            handler = Handler((self._func, instance), self._connection_strings,
                              instance if self._ob is None else self._ob())
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
            connection. A weak reference to this object is stored.
    """

    _count = 0

    def __init__(self, func, connection_strings, ob):
        Handler._count += 1
        self._id = 'h%i' % Handler._count  # to ensure a consistent event order

        # Store objects using a weakref.
        # - ob1 is the HasEvents object of which the connect() method was called
        #   to create the handler. Connection strings are relative to this object.
        # - ob2 is the object to be passed to func (if it is a method). Is often
        #   the same as ob1, but not per see. Can be None.
        self._ob1 = weakref.ref(ob)

        # Get unbounded version of bound methods.
        self._ob2 = None  # if None, its regarded a regular function
        if isinstance(func, tuple):
            self._ob2 = weakref.ref(func[1])
            func = func[0]
        if getattr(func, '__self__', None) is not None:  # builtin funcs have __self__
            if getattr(func, '__func__', None) is not None:
                self._ob2 = weakref.ref(func.__self__)
                func = func.__func__

        # Store func, name, and docstring (e.g. for sphinx docs)
        assert callable(func)
        self._func = func
        self._func_once = func
        self._name = func.__name__
        self.__doc__ = '*%s*: %s' % ('event handler', func.__doc__ or self._name)

        self._init(connection_strings)
    
    def _init(self, connection_strings):
        """ Init of this handler that is compatible with PyScript.
        """
        
        ichars = '0123456789_abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
        self._connections = []
        
        # Notes on connection strings:
        # * The string can have a "!" at the start to suppress warnings for
        #   connections to unknown event types.
        # * The string can have a label suffix separated by a colon. The
        #   label may consist of any chars.
        # * Connection strings consist of parts separated by dots.
        # * Each part can end with one star ('*'), indicating that connections
        #   should be made for each item in the list, or two stars, indicating
        #   that connections should be made *recursively* for each item in the
        #   list (a.k.a. a deep connector).
        # * Stripped of '*', each part must be a valid identifier.
        # * An extreme example: "!foo.bar*.spam.eggs**:meh"
        
        for fullname in connection_strings:
            # Separate label and exclamation mark from the string path
            force = fullname.startswith('!')
            s, _, label = fullname.lstrip('!').partition(':')
            s0 = s
            # Backwards compat: "foo.*.bar* becomes "foo*.bar"
            if '.*.' in s + '.':
                s = s.replace('.*', '*')
                console.warn('Connection string syntax "foo.*.bar" is deprecated, '
                             'use "%s" instead of "%s":.' % (s, s0))
            # Help put exclamation at the start
            if '!' in s:
                s = s.replace('!', '')
                force = True
                console.warn('Exclamation marks in connection strings must come at '
                             'the very start, use "!%s" instead of "%s".' % (s, s0))
            # Check that all parts are identifiers
            parts = s.split('.')
            for part in parts:
                part = part.rstrip('*')
                is_identifier = bool(part)
                for c in part:
                    is_identifier = is_identifier and (c in ichars)
                if not is_identifier:
                    raise ValueError('Connection string %r contains '
                                     'non-identifier part %r' % (s, part))
            # Init connection
            d = Dict()  # don't do Dict(foo=x) bc PyScript only supports that for dict
            self._connections.append(d)
            d.fullname = fullname  # original, used in logs, so is searchable
            d.parts = parts
            d.type = parts[-1].rstrip('*') + ':' + (label or self._name)
            d.force = force
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
        if self._ob2 is not None:
            if self._ob2() is not None:
                res = func(self._ob2(), *events)
            else:
                # We detected that the object that wants the events no longer exist
                self.dispose()
                return
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
                #setTimeout(self._handle_now_callback.bind(self), 0)
                loop.call_later(self._handle_now_callback.bind(self))
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
        # Collect pending events and clear current list
        events, reconnect = self._collect()
        self._pending = []
        # Reconnect (dynamism)
        for index in reconnect:
            self._connect_to_event(index)
        # Collect newly created events (corresponding to props)
        events2, reconnect2 = self._collect()
        if not len(reconnect2):
            events = events + events2
            self._pending = []
        # Handle events
        if len(events):
            if not this_is_js():
                logger.debug('Handler %s is processing %i events' %
                            (self._name, len(events)))
            try:
                self(*events)
            except Exception as err:
                if this_is_js():
                    console.error(err)
                else:
                    err.skip_tb = 2
                    logger.exception(err)

    def _collect(self):
        """ Get list of events and reconnect-events from list of pending events.
        """
        events = []
        reconnect = []
        for label, ev in self._pending:
            if label.startswith('reconnect_'):
                index = int(label.split('_')[-1])
                reconnect.append(index)
            else:
                events.append(ev)
        return events, reconnect

    ## Connecting

    def dispose(self):
        """ Cleanup any references.

        Disconnects all connections, and cancel all pending events.
        """
        if not this_is_js():
            logger.debug('Disposing Handler %r ' % self)
        for connection in self._connections:
            while len(connection.objects):
                ob, type = connection.objects.pop(0)
                ob.disconnect(type, self)
        while len(self._pending):
            self._pending.pop()  # no list.clear on legacy py

    def _clear_hasevents_refs(self, ob):
        """ Clear all references to the given HasEvents instance. This is
        called from a HasEvents' dispose() method. This handler remains
        working, but wont receive events from that object anymore.
        """
        for connection in self._connections:
            for i in range(len(connection.objects)-1, -1, -1):
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
            ob, type = connection.objects.pop(0)
            ob.disconnect(type, self)

        # Obtain root object and setup connections
        ob = self._ob1()
        if ob is not None:
            self._seek_event_object(index, connection.parts, ob)

        # Verify
        if not connection.objects:
            raise RuntimeError('Could not connect to %r' % connection.fullname)

        # Connect
        for ob, type in connection.objects:
            ob._register_handler(type, self, connection.force)

    def _seek_event_object(self, index, path, ob):
        """ Seek an event object based on the name (PyScript compatible).
        The path is a list: the path to the event, the last element being the
        event type.
        """
        connection = self._connections[index]

        # Should we make connection or stop?
        if ob is None or len(path) == 0:
            return  # We cannot seek further
        if len(path) == 1:
            # Path only consists of event type now: make connection
            # connection.type consists of event type name (no stars) plus a label
            if hasattr(ob, '_IS_HASEVENTS'):
                connection.objects.append((ob, connection.type))
            # Reached end or continue?
            if not path[0].endswith('**'):
                return
        
        # Resolve name
        obname_full, path = path[0], path[1:]
        obname = obname_full.rstrip('*')
        selector = obname_full[len(obname):]

        # Internally, 3-star notation is used for optional selectors
        if selector == '***':
            self._seek_event_object(index, path, ob)
        # Select object
        if hasattr(ob, '_IS_HASEVENTS') and obname in ob.__properties__:
            name_label = obname + ':reconnect_' + str(index)
            connection.objects.append((ob, name_label))
            new_ob = getattr(ob, obname, None)
        else:
            new_ob = getattr(ob, obname, None)
        # Look inside?
        if len(selector) and selector in '***' and isinstance(new_ob, (tuple, list)):
            if len(selector) > 1:
                path = [obname + '***'] + path  # recurse (avoid insert for space)
            for sub_ob in new_ob:
                self._seek_event_object(index, path, sub_ob)
            return
        elif selector == '*':  # "**" is recursive, so allow more
            t = "Invalid connection {name_full} because {name} is not a tuple/list."
            raise RuntimeError(t.replace("{name_full}", obname_full)
                .replace("{name}", obname))
        else:
            return self._seek_event_object(index, path, new_ob)
