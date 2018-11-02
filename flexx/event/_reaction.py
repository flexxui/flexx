"""
Implements the reaction decorator, class and desciptor.
"""

# Note: there are some unusual constructs here, such as ``if xx is True``.
# These are there to avoid inefficient JS code as this code is transpiled
# using PScript. This code is quite performance crirical.

import weakref
import inspect

from ._loop import this_is_js
from ._action import BaseDescriptor
from ._dict import Dict
from . import logger


window = None
console = logger


def looks_like_method(func):
    if hasattr(func, '__func__'):
        return False  # this is a bound method
    try:
        return list(inspect.signature(func).parameters)[0] in ('self', 'this')
    except (TypeError, IndexError, ValueError):
        return False


def reaction(*connection_strings, mode='normal'):
    """ Decorator to turn a method of a Component into a
    :class:`Reaction <flexx.event.Reaction>`.

    A reaction can be connected to multiple event types. Each connection
    string represents an event type to connect to.

    Also see the
    :func:`Component.reaction() <flexx.event.Component.reaction>` method.

    .. code-block:: py

        class MyObject(event.Component):

            @event.reaction('first_name', 'last_name')
            def greet(self, *events):
                print('hello %s %s' % (self.first_name, self.last_name))

    A reaction can operate in a few different modes. By not specifying any
    connection strings, the mode is "auto": the reaction will automatically
    trigger when any of the properties used in the function changes.
    See :func:`get_mode() <flexx.event.Reaction.get_mode>` for details.
    
    Connection string follow the following syntax rules:
    
    * Connection strings consist of parts separated by dots, thus forming a path.
      If an element on the path is a property, the connection will automatically
      reset when that property changes (a.k.a. dynamism, more on this below).
    * Each part can end with one star ('*'), indicating that the part is a list
      and that a connection should be made for each item in the list.
    * With two stars, the connection is made *recursively*, e.g. "children**"
      connects to "children" and the children's children, etc.
    * Stripped of '*', each part must be a valid identifier (ASCII).
    * The total string optionally has a label suffix separated by a colon. The
      label itself may consist of any characters.
    * The string can have a "!" at the very start to suppress warnings for
      connections to event types that Flexx is not aware of at initialization
      time (i.e. not corresponding to a property or emitter).
    
    An extreme example could be ``"!foo.children**.text:mylabel"``, which connects
    to the "text" event of the children (and their children, and their children's
    children etc.) of the ``foo`` attribute. The "!" is common in cases like
    this to suppress warnings if not all children have a ``text`` event/property.
    
    """
    if (not connection_strings):
        raise TypeError('reaction() needs one or more arguments.')

    # Validate mode parameter
    mode = mode or 'normal'  # i.e. allow None
    if not isinstance(mode, str):
        raise TypeError('Reaction mode must be a string.')
    mode = mode.lower()
    if mode not in ('normal', 'greedy', 'auto'):
        raise TypeError('Reaction mode must "normal", "greedy" or "auto".')

    # Extract function if we can
    func = None
    if len(connection_strings) == 1 and callable(connection_strings[0]):
        func = connection_strings[0]
        connection_strings = []

    for s in connection_strings:
        if not (isinstance(s, str) and len(s) > 0):
            raise TypeError('Connection string must be nonempty strings.')

    def _connect(func):
        if not callable(func):
            raise TypeError('reaction() decorator requires a callable.')
        if not looks_like_method(func):
            raise TypeError('reaction() decorator requires a method '
                            '(first arg must be self).')
        return ReactionDescriptor(func, mode, connection_strings)

    if func is not None:
        return _connect(func)
    else:
        return _connect


class ReactionDescriptor(BaseDescriptor):
    """ Class descriptor for reactions.
    """

    def __init__(self, func, mode, connection_strings, ob=None):
        self._name = func.__name__
        self._func = func
        self._mode = mode
        if len(connection_strings) == 0:
            self._mode = 'auto'
        self._connection_strings = connection_strings
        self._ob = None if ob is None else weakref.ref(ob)
        self.__doc__ = self._format_doc('reaction', self._name, func.__doc__)

    def __get__(self, instance, owner):
        if instance is None:
            return self

        private_name = '_' + self._name + '_reaction'
        try:
            reaction = getattr(instance, private_name)
        except AttributeError:
            reaction = Reaction(instance if self._ob is None else self._ob(),
                                (self._func, instance),
                                self._mode,
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
        # This is used in e.g. flexx.app
        return [s for s in self._connection_strings if '.' not in s]


class Reaction:
    """ Reaction objects are wrappers around Component methods. They connect
    to one or more events. This class should not be instantiated directly;
    use ``event.reaction()`` or ``Component.reaction()`` instead.
    """

    _count = 0

    def __init__(self, ob, func, mode, connection_strings):
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
        assert mode in ('normal', 'greedy', 'auto')
        self._func = func
        self._func_once = func
        self._mode = mode
        self._name = func.__name__
        self.__doc__ = BaseDescriptor._format_doc('reaction', self._name, func.__doc__)

        self._init(connection_strings)

    def _init(self, connection_strings):
        """ Init of this reaction that is compatible with PScript.
        """

        ichars = '0123456789_abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'

        # Init explicit connections: (connection-object, type) tuples
        self._connections = []
        # Init implicit connections: (component, type) tuples
        self._implicit_connections = []

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
        for ic in range(len(connection_strings)):
            fullname = connection_strings[ic]
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
            for ipart in range(len(parts)):
                part = parts[ipart].rstrip('*')
                is_identifier = len(part) > 0
                for i in range(len(part)):
                    is_identifier = is_identifier and (part[i] in ichars)
                if is_identifier is False:
                    raise ValueError('Connection string %r contains '
                                     'non-identifier part %r' % (s, part))
            # Init connection
            d = Dict()  # don't do Dict(foo=x) bc PScript only supports that for dict
            self._connections.append(d)
            d.fullname = fullname  # original, used in logs, so is searchable
            d.parts = parts
            d.type = parts[-1].rstrip('*') + ':' + (label or self._name)
            d.force = force
            d.objects = []

        # Connect
        for ic in range(len(self._connections)):
            self.reconnect(ic)

    def __repr__(self):
        c = '+'.join([str(len(c.objects)) for c in self._connections])
        cname = self.__class__.__name__
        t = '<%s %r (%s) with %s connections at 0x%x>'
        return t % (cname, self._name, self._mode, c, id(self))

    def get_mode(self):
        """ Get the mode for this reaction:

        * 'normal': events are handled in the order that they were emitted.
          Consequently, there can be multiple calls per event loop iteration
          if other reactions were triggered as well.
        * 'greedy': this reaction receives all its events (since the last event
          loop iteration) in a single call (even if this breaks the order of
          events with respect to other reactions). Use this when multiple related
          events must be handled simultenously (e.g. when syncing properties).
        * 'auto': this reaction tracks what properties it uses, and is
          automatically triggered when any of these properties changes. Like
          'greedy' there is at most one call per event loop iteration.
          Reactions with zero connection strings always have mode 'auto'.

        The 'normal' mode generally offers the most consistent behaviour.
        The 'greedy' mode allows the event system to make some optimizations.
        Combined with the fact that there is at most one call per event loop
        iteration, this can provide higher performance where it matters.
        Reactions with mode 'auto' can be a convenient way to connect things
        up. Although it allows the event system to make the same optimizations
        as 'greedy', it also needs to reconnect the reaction after each time
        it is called, which can degregade performance especially if many
        properties are accessed by the reaction.
        """
        return self._mode

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
            else:  # pragma: no cover
                # We detected that the object that wants the events no longer exist
                self.dispose()
                return
        else:
            res = func(*events)
        return res

    ## Connecting

    def dispose(self):
        """ Disconnect all connections so that there are no more references
        to components.
        """
        if len(self._connections) == 0 and len(self._implicit_connections) == 0:
            return
        if not this_is_js():
            self._ob1 = lambda: None
            logger.debug('Disposing reaction %r ' % self)
        while len(self._implicit_connections):
            ob, type = self._implicit_connections.pop(0)
            ob.disconnect(type, self)
        for ic in range(len(self._connections)):
            connection = self._connections[ic]
            while len(connection.objects) > 0:
                ob, type = connection.objects.pop(0)
                ob.disconnect(type, self)
        self._connections = []

    def _update_implicit_connections(self, connections):
        """ Update the list of implicit (i.e. automatic) connections.
        Used by the loop.
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
        for i in range(len(self._implicit_connections)-1, -1, -1):
            if self._implicit_connections[i][0] is ob:
                self._implicit_connections.pop(i)
        for ic in range(len(self._connections)):
            connection = self._connections[ic]
            for i in range(len(connection.objects)-1, -1, -1):
                if connection.objects[i][0] is ob:
                    connection.objects.pop(i)

    def reconnect(self, index):
        """ (re)connect the index'th connection.
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
        if len(new_objects) == 0:
            raise RuntimeError('Could not connect to %r' % connection.fullname)

        # Reconnect in a smart way
        self._connect_and_disconnect(old_objects, new_objects, connection.force)

    def _connect_and_disconnect(self, old_objects, new_objects, force=False):
        """ Update connections by disconnecting old and connecting new,
        but try to keep connections that do not change.
        """

        # Keep track of what connections we skip, i.e. which we should not remove.
        # Otherwise we may remove duplicate objects. See issue #460.
        should_stay = {}

        # Skip common objects from the start
        i1 = 0
        while (i1 < len(new_objects) and i1 < len(old_objects) and
               new_objects[i1][0] is old_objects[i1][0] and
               new_objects[i1][1] == old_objects[i1][1]):
            should_stay[new_objects[i1][0].id + '-' + new_objects[i1][1]] = True
            i1 += 1
        # Skip common objects from the end
        i2, i3 = len(new_objects) - 1, len(old_objects) - 1
        while (i2 >= i1 and i3 >= i1 and
               new_objects[i2][0] is old_objects[i3][0] and
               new_objects[i2][1] == old_objects[i3][1]):
            should_stay[new_objects[i2][0].id + '-' + new_objects[i2][1]] = True
            i2 -= 1
            i3 -= 1
        # Disconnect remaining old
        for i in range(i1, i3+1):
            ob, type = old_objects[i]
            if should_stay.get(ob.id + '-' + type, False) is False:
                ob.disconnect(type, self)
        # Connect remaining new
        for i in range(i1, i2+1):
            ob, type = new_objects[i]
            ob._register_reaction(type, self, force)

    def _seek_event_object(self, index, path, ob):
        """ Seek an event object based on the name (PScript compatible).
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
            for isub in range(len(new_ob)):
                self._seek_event_object(index, path, new_ob[isub])
            return
        elif selector == '*':  # "**" is recursive, so allow more
            t = "Invalid connection {name_full} because {name} is not a tuple/list."
            raise RuntimeError(t.replace("{name_full}", obname_full)
                .replace("{name}", obname))
        else:
            return self._seek_event_object(index, path, new_ob)
