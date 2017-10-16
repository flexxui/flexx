"""
Implements the reaction decorator, class and desciptor.
"""

import weakref
import inspect

from ._action import BaseDescriptor
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


def reaction(*connection_strings):
    """ Decorator to turn a method of Component into a
    :class:`Reaction <flexx.event.Reaction>`.

    A method can be connected to multiple event types. Each connection
    string represents an event type to connect to. Read more about
    dynamism and labels for further information on the possibilities
    of connection strings.

    To connect functions or methods to an event from another Component
    object, use that object's
    :func:`Component.connect()<flexx.event.Component.connect>` method.

    .. code-block:: py

        class MyObject(event.Component):
        
            @event.reaction('first_name', 'last_name')
            def greet(self, *events):
                print('hello %s %s' % (self.first_name, self.last_name))
    """
    if (not connection_strings):
        raise RuntimeError('reaction() needs one or more arguments.')
    
    # Extract function if we can
    func = None
    if callable(connection_strings[0]):
        func = connection_strings[0]
        connection_strings = connection_strings[1:]
    elif callable(connection_strings[-1]):
        func = connection_strings[-1]
        connection_strings = connection_strings[:-1]
    
    for s in connection_strings:
        if not (isinstance(s, str) and len(s) > 0):
            raise ValueError('Connection string must be nonempty strings.')

    def _connect(func):
        if not callable(func):
            raise TypeError('reaction() decorator requires a callable.')
        if not looks_like_method(func):
            raise TypeError('reaction() decorator requires a method '
                            '(first arg must be self).')
        return ReactionDescriptor(func, connection_strings)

    if func is not None:
        return _connect(func)
    else:
        return _connect


class ReactionDescriptor(BaseDescriptor):
    """ Class descriptor for reactions.
    """
    
    def __init__(self, func, connection_strings, ob=None):
        self._func = func
        self._name = func.__name__
        self._ob = None if ob is None else weakref.ref(ob)
        self._connection_strings = connection_strings
        self.__doc__ = '*%s*: %s' % ('event reaction', func.__doc__ or self._name)

    def __get__(self, instance, owner):
        if instance is None:
            return self

        private_name = '_' + self._name + '_reaction'
        try:
            reaction = getattr(instance, private_name)
        except AttributeError:
            reaction = Reaction(instance if self._ob is None else self._ob(),
                                (self._func, instance),
                                self._connection_strings)
            setattr(instance, private_name, reaction)

        # Make the reaction use *our* func one time. In most situations
        # this is the same function that the reaction has, but not when
        # using super(); i.e. this allows a reaction to call the same
        # reaction of its super class.
        reaction._use_once(self._func)
        return reaction

    @property
    def local_connection_strings(self):
        """ List of connection strings that are local to the object.
        """
        return [s for s in self._connection_strings if '.' not in s]


class Reaction:
    """ Reaction objects are wrappers around Component methods. They connected
    to one or more events. This class should not be instantiated directly;
    use ``event.reaction()`` or ``Component.connect()`` instead.
    """

    _count = 0

    def __init__(self, ob, func, connection_strings):
        Reaction._count += 1
        self._id = 'r%i' % Reaction._count  # to ensure a consistent event order

        # Store objects using a weakref.
        # - ob1 is the Component object of which the connect() method was called
        #   to create the reaction. Connection strings are relative to this object.
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
        self.__doc__ = '*%s*: %s' % ('event reaction', func.__doc__ or self._name)

        self._init(connection_strings)
    
    def _init(self, connection_strings):
        """ Init of this reaction that is compatible with PyScript.
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

        # Pending events for this reaction
        self._scheduled_update = False
        self._pending = []  # pending events
        
        # Implicit connections
        self._implicit_connections = []  # list of (component, type) tuples
        
        # Connect
        for index in range(len(self._connections)):
            self._connect_to_event(index)

    def __repr__(self):
        c = '+'.join([str(len(c.objects)) for c in self._connections])
        cname = self.__class__.__name__
        return '<%s %r with %s connections at 0x%x>' % (cname, self._name, c, id(self))
    
    def is_explicit(self):
        """ Whether this reaction is explicit (has connection strings),
        or implicit (auto-connects to used properties).
        """
        return len(self._connections) > 0
    
    def get_name(self):
        """ Get the name of this reaction, usually corresponding to the name
        of the function that this reaction wraps.
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
        """ Call the reaction function.
        """
        func = self._func_once
        self._func_once = self._func
        if self._ob2 is not None:
            if self._ob2() is not None:
                res = func(self._ob2(), *events)
            else:
                # We detected that the object that wants the events no longer exist
                self.dispose()
                return
        else:
            res = func(*events)
        return res

    ## Connecting

    def dispose(self):
        """ Cleanup any references.

        Disconnects all connections, and cancel all pending events.
        """
        if not this_is_js():
            logger.debug('Disposing reaction %r ' % self)
        for connection in self._connections:
            while len(connection.objects):
                ob, type = connection.objects.pop(0)
                ob.disconnect(type, self)
        self._connections = []
        while len(self._pending):
            self._pending.pop()  # no list.clear on legacy py
    
    def _filter_events(self, events):
        """ Filter events, taking out the events for reconnections.
        Used by the loop.
        """
        # Filter
        filtered_events = []
        reconnect = {}  # poor man's set
        for ev in events:
            if ev.label.startswith('reconnect_'):
                index = int(ev.label.split('_')[-1])
                reconnect[index] = index
            else:
                filtered_events.append(ev)
        # Reconnect
        for index in reconnect:
            self._connect_to_event(index)
        # Return shorter list
        return events
    
    def _update_implicit_connections(self, connections):
        """ Update the list of implicit connections. Used by the loop.
        """
        # Init - each connection is a (component, type) tuple
        old_conns = self._implicit_connections
        new_conns = connections
        self._implicit_connections = new_conns
        
        # Reconnect in a smart way
        self._connect_and_disconnect(old_conns, new_conns)
    
    def _clear_component_refs(self, ob):
        """ Clear all references to the given Component instance. This is
        called from a Component' dispose() method. This reaction remains
        working, but wont receive events from that object anymore.
        """
        for connection in self._connections:
            for i in range(len(connection.objects)-1, -1, -1):
                if connection.objects[i][0] is ob:
                    connection.objects.pop(i)

        # Do not clear pending events. This reaction is assumed to continue
        # working, and should thus handle its pending events at some point,
        # at which point it cannot hold any references to ob anymore.

    def _connect_to_event(self, index):
        """ Connect one connection.
        """
        connection = self._connections[index]

        # Prepare disconnecting
        old_objects = connection.objects  # (ob, type) tuples
        connection.objects = []
        
        # Obtain root object and setup connections
        ob = self._ob1()
        if ob is not None:
            self._seek_event_object(index, connection.parts, ob)
        new_objects = connection.objects
        
        # Verify
        if not new_objects:
            raise RuntimeError('Could not connect to %r' % connection.fullname)
        
        # Reconnect in a smart way
        self._connect_and_disconnect(old_objects, new_objects, connection.force)
    
    def _connect_and_disconnect(self, old_objects, new_objects, force=False):    
        """ Update connections by disconnecting old and connecting new,
        but try to keep connections that do not change.
        """
    
        # Skip common objects from the start
        i1 = 0
        while (i1 < len(new_objects) and i1 < len(old_objects) and
               new_objects[i1][0] is old_objects[i1][0] and
               new_objects[i1][1] == old_objects[i1][1]):
            i1 += 1
        # Skip common objects from the end
        i2, i3 = len(new_objects) - 1, len(old_objects) - 1
        while (i2 >= i1 and i3 >= i1 and
               new_objects[i2][0] is old_objects[i3][0] and
               new_objects[i2][1] == old_objects[i3][1]):
            i2 -= 1
            i3 -= 1
        # Disconnect remaining old
        for ob, type in old_objects[i1:i3+1]:
            ob.disconnect(type, self)
        # Connect remaining new
        for ob, type in new_objects[i1:i2+1]:
            ob._register_reaction(type, self, force)

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
            if hasattr(ob, '_IS_COMPONENT'):
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
        if hasattr(ob, '_IS_COMPONENT') and obname in ob.__properties__:
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
