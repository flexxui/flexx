import sys
import inspect
import weakref

from ._properties import Property

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
def connect(*event_names):
    """ Decorator to connect a handler to one or more events.
    
    Example:
        
        .. code-block:: py
            
            @event.connect('first_name', 'last_name')
            def greet(*events):
                print('hello %s %s' % (self.first_name, self.last_name))
    """
    # todo: how to create event full_name?
    
    if (not event_names) or (event_names and callable(event_names[0])):
        raise ValueError('Connect decorator needs one or more event names.')
    
    def _connect(func):
        frame = sys._getframe(1)
        if '__module__' in frame.f_locals:
            return HandlerDescriptor(func, event_names, frame)
        else:
            return Handler(func, event_names, frame)
        return s
    return _connect


class ObjectFrame(object):
    """ A proxy frame that gives access to the class instance (usually
    from HasEvents) as a frame, combined with the frame that the class
    was defined in.
    """
    
    # We need to store the frame. If we stored the f_locals dict, it
    # would not be up-to-date by the time we need it. I suspect that
    # getattr(frame, 'f_locals') updates the dict.
    
    def __init__(self, ob, frame):
        self._ob = weakref.ref(ob)
        self._frame = frame
    
    @property
    def f_locals(self):
        locals = self._frame.f_locals.copy()
        ob = self._ob()
        if ob is not None:
            locals.update(ob.__dict__)
            # Handle signals. Not using __handles__; works on any class
            for key in dir(ob.__class__):
                if key.startswith('__'):
                    continue
                val = getattr(ob.__class__, key)
                # todo: look inside properties
                if isinstance(val, Property):  # todo: also readonly
                    private_name = '_' + key + '_prop'
                    if private_name in locals:
                        locals[key] = locals[private_name]
        return locals
    
    @property
    def f_globals(self):
        return self._frame.f_globals
    
    @property
    def f_back(self):
        return ObjectFrame(self._ob(), self._frame.f_back)


class HandlerDescriptor:
    """ Class descriptor for handlers.
    """
    def __init__(self, func, upstream, frame):
        if not callable(func):
            raise ValueError('Handler needs a callable')
        self._func = func
        self._name = func.__name__  # updated by HasEvents meta class
        self._upstream_given = upstream
        self._frame = frame
    
    def __repr__(self):
        cls_name = self.__class__.__name__
        return '<%s for %s at 0x%x>' % (cls_name, self._name, id(self))
        
    def __set__(self, obj, value):
        raise ValueError('Cannot overwrite handler %r.' % self._name)
    
    def __delete__(self, obj):
        raise ValueError('Cannot delete handler %r.' % self._name)
    
    def __get__(self, instance, owner):
        if instance is None:
            return self
        
        private_name = '_' + self._name + '_handler'
        try:
            return getattr(instance, private_name)
        except AttributeError:
            frame = ObjectFrame(instance, self._frame.f_back)
            new = Handler(self._func, self._upstream_given, frame, instance)
            setattr(instance, private_name, new)
            return new


class Handler:
    """ Wrapper around a function object to connect it to one or more events.
    This class should not be instantiated directly; use the decorators instead.
    """
    # todo: need any of this?
    _IS_HANDLER = True  # poor man's isinstance in JS (because class name mangling)
    _active = True
    _count = 0
    
    def __init__(self, func, upstream, frame=None, ob=None):
        # Check and set func
        if not callable(func):
            raise ValueError('Handler needs a callable')
        self._func = func
        self._name = func.__name__
        Handler._count += 1
        self._id = str(Handler._count)  # to ensure a consistent event order
        
        # Set docstring; this appears correct in sphinx docs
        self.__doc__ = '*%s*: %s' % (self.__class__.__name__,
                                     func.__doc__ or self._name)
        
        # Check and set dependencies
        upstream = [s for s in upstream]
        for s in upstream:
            assert isinstance(s, str) and len(s) > 0
        self._upstream_given = [s for s in upstream]
        self._upstream = []
        self._upstream_reconnect = []
        
        # Pending events for this handler
        self._scheduled_update = False
        self._need_connect = False
        self._pending = []  # (label, ev) tuples
        
        # Frame and object
        self._frame = frame or sys._getframe(1)
        self._ob = weakref.ref(ob) if (ob is not None) else None
        
        # Get whether function is a method
        try:
            self._func_is_method = inspect.getargspec(func)[0][0] in ('self', 'this')
        except (TypeError, IndexError):
            self._func_is_method = False
        
        # Connecting
        self._not_connected = 'No connection attempt yet.'
        self.connect(False)

    def __repr__(self):
        conn = '(not connected)' if self.not_connected else '(connected)'
        cls_name = self.__class__.__name__
        return '<%s %r %s at 0x%x>' % (cls_name, self._name, conn, id(self))
    
    @property
    def _self(self):
        """ The HasSignals instance that this signal is associated with
        (stored as a weak reference internally). None for plain signals.
        """
        if self._ob is not None:
            return self._ob()
    
    @property
    def name(self):
        """ The name of this signal, usually corresponding to the name
        of the function that this signal wraps.
        """
        return self._name
    
    ## Calling / handling
    
    def __call__(self):
        """ Call the handler function.
        """
        if self._func_is_method and self._ob is not None:
            return self._func(self._ob())
        else:
            return self._func()
    
    def add_pending_event(self, ev, reconnect=False):
        """ Add an event object to be handled at the next event loop
        iteration. Called from HasEvents.dispatch().
        """
        self._need_connect = self._need_connect or reconnect
        if not self._scheduled_update:
            self._scheduled_update = True
            loop.call_later(self.handle_now)  # register only once
        self._pending.append((ev.label, ev))
    
    def handle_now(self):
        """ Invoke a call to the handler with all pending events. This
        is normally called in a next event loop iteration when an event
        is scheduled for this handler, but it can also be called to
        force the handler to process pending events *now*.
        """
        self._scheduled_update = False
        # Connect?
        if self._need_connect:
            self._need_connect = False
            self.connect(False)  # todo: this should not fail
        # Event objects are shared between handlers, but each set its own label)
        self._pending, events = [], self._pending
        for label, ev in events:
            ev.label = label
        events = [ev for label, ev in events]
        # Handle events
        if not events:
            pass
        elif self._func_is_method and self._ob is not None:
            return self._func(self._ob(), *events)
        else:
            return self._func(*events)
    
    
    ## Connecting
    
    def connect(self, raise_on_fail=True):
        """ Connect to HasEvents objects.
        
        The event names that were provided as a string are resolved to
        get the corresponding HasEvent objects, and the current handler
        is subscribed to these events.
        
        If resolving the signals from the strings fails, raises an
        error. Unless ``raise_on_fail`` is ``False``, in which case this
        returns ``True`` on success and ``False`` on failure.
        
        This function is automatically called during initialization,
        and .... ???
        """
        # todo: can we not connect per event-path? Now we reconnect all signals if we need reconnect
        
        # First disconnect
        while len(self._upstream):
            ob, name = self._upstream.pop(0)
            ob._unregister_handler(name, self)
        while len(self._upstream_reconnect):  # len() for PyScript compat
            ob, name = self._upstream_reconnect.pop(0)
            ob._unregister_handler(name, self)
        
        # Resolve signals
        self._not_connected = self._resolve_signals()
        
        # Subscribe (on a fail, the _upstream_reconnect can still be non-empty)
        for ob, name in self._upstream:
            ob._register_handler(name, self)
        for ob, name in self._upstream_reconnect:
            ob._register_handler_reconnect(name, self)  # todo: should invoke a reconnect
        
        # Fail?
        if self._not_connected:
            if raise_on_fail:
                raise RuntimeError('Connection error in signal %r: %s' % 
                                   (self._name, self._not_connected))
            return False
        
        return True
    
    def disconnect(self, destroy=True):
        """ Disconnect this signal, unsubscribing it from the upstream
        signals. If destroy is True (default), will also clear the
        internal frame object, allowing unused objects to be deleted.
        """
        # todo: rename to dispose?
        # Disconnect upstream
        while len(self._upstream):  # len() for PyScript compat
            ob, name = self._upstream.pop(0)
            ob._unregister_handler(name, self)
        self._not_connected = 'Explicitly disconnected via disconnect()'
        if destroy:
            self._frame = None
    
    def _seek_signal(self, fullname, path, ob, name):
        """ Seek a signal based on the name. Used by _resolve_signals.
        This bit is PyScript compatible (_resolve_signals is not).
        """
        if fullname == 'sub.bar':
            fullname = fullname
        # Done traversing name: add to list or fail
        if ob is undefined or len(path) == 0:
            if ob is undefined:
                return 'Cannot find HasEvents object for "%s".' % fullname
            if not hasattr(ob, '_IS_HASSIGNALS'):
                return 'Object "%s" is not on an HasEvents object.' % fullname
            self._upstream.append((ob, name))
            return None  # ok
        
        # Resolve name
        ob_name, path = path[0], path[1:]
        if getattr(getattr(ob.__class__, ob_name, None), '_IS_PROP', False):
            # todo: make .__class__ work in PyScript
            self._upstream_reconnect.append((ob, ob_name))
            ob = getattr(ob, ob_name)
        elif ob_name == '*' and isinstance(ob, (tuple, list)):
            for sub_ob in ob:
                msg = self._seek_signal(fullname, path, sub_ob, name)
                if msg:
                    return msg
            return None  # ok
        else:
            ob = getattr(ob, ob_name, undefined)
        return self._seek_signal(fullname, path, ob, name)
    
    def _resolve_signals(self):
        """ Get signals from their string path. Return value to store
        in _not_connected (False means success). Should only be called from
        connect().
        """
        
        self._upstream = []
        self._upstream_reconnect = []
        
        for fullname in self._upstream_given:
            nameparts = fullname.split('.')
            path, name = nameparts[:-1], nameparts[-1]  # path to HasEvents ob
            # Obtain root object
            ob = self._ob() if self._ob else None
            if not path:
                pass  # it must be an event on *our* object
            elif ob is not None and hasattr(ob, path[0]):
                pass  # what we're looking seems to be on our object
            else: 
                f = self._frame  # look in locals and globals
                ob = f.f_locals.get(path[0], f.f_globals.get(path[0], undefined))
                path = path[1:]
            msg = self._seek_signal(fullname, path, ob, name)
            # todo: we can be connected to one signal and not to another, right?
            if msg:
                self._upstream = []
                return msg
        
        return False  # no error
    
    @property
    def not_connected(self):
        """ False when not all signals are connected. Otherwise this
        is a string with a message why the signal is not connected.
        """
        return self._not_connected
