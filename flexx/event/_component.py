"""
Implements the Component class; the core class that has properties,
actions that mutate the properties, and reactions that react to the
events and changes in properties.
"""

import sys

from ._dict import Dict
from ._attribute import Attribute
from ._action import ActionDescriptor, Action
from ._reaction import ReactionDescriptor, Reaction, looks_like_method
from ._property import Property
from ._emitter import EmitterDescriptor
from ._loop import loop, this_is_js
from . import logger


setTimeout = console = None


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


def new_type(name, *args, **kwargs):  # pragma: no cover
    """ Alternative for type(...) to be legacy-py compatible.
    """
    name = name.encode() if sys.version_info[0] == 2 else name
    return type(name, *args, **kwargs)


class ComponentMeta(type):
    """ Meta class for Component
    * Set the name of property desciptors.
    * Set __actions__, __reactions__, __emitters__ and __properties__ class attributes.
    * Create private methods (e.g. mutator functions and prop validators).
    """

    def __init__(cls, name, bases, dct):
        cls._finish_properties(dct)
        cls._init_hook1(name, bases, dct)
        cls._set_summaries()
        cls._init_hook2(name, bases, dct)
        type.__init__(cls, name, bases, dct)

    def _init_hook1(cls, name, bases, dct):
        """ Overloaded in flexx.app.AppComponentMeta.
        """
        pass

    def _init_hook2(cls, name, bases, dct):
        """ Overloaded in flexx.app.AppComponentMeta.
        """
        pass

    def _set_cls_attr(cls, dct, name, att):
        dct[name] = att
        setattr(cls, name, att)

    def _finish_properties(cls, dct):
        """ Finish properties:

        * Create a mutator function for convenience.
        * Create validator function.
        * If needed, create a corresponding set_xx action.
        """
        for name in list(dct.keys()):
            if name.startswith('__'):
                continue
            val = getattr(cls, name)
            if isinstance(val, type) and issubclass(val, (Attribute, Property)):
                raise TypeError('Attributes and Properties should be instantiated, '
                                'use ``foo = IntProp()`` instead of ``foo = IntProp``.')
            elif isinstance(val, Attribute):
                val._set_name(name)  # noqa
            elif isinstance(val, Property):
                val._set_name(name)  # noqa
                # Create validator method
                cls._set_cls_attr(dct, '_' + name + '_validate', val._validate_py)
                # Create mutator method
                cls._set_cls_attr(dct, '_mutate_' + name, val.make_mutator())
                # Create setter action?
                action_name = ('_set' if name.startswith('_') else 'set_') + name
                if val._settable and not hasattr(cls, action_name):
                    action_des = ActionDescriptor(val.make_set_action(), action_name,
                                                  'Setter for the %r property.' % name)
                    cls._set_cls_attr(dct, action_name, action_des)

    def _set_summaries(cls):
        """ Analyse the class and set lists __actions__, __emitters__,
        __properties__, and __reactions__.
        """

        attributes = {}
        properties = {}
        actions = {}
        emitters = {}
        reactions = {}

        for name in dir(cls):
            if name.startswith('__'):
                continue
            val = getattr(cls, name)
            if isinstance(val, Attribute):
                attributes[name] = val
            elif isinstance(val, Property):
                properties[name] = val
            elif isinstance(val, ActionDescriptor):
                actions[name] = val
            elif isinstance(val, ReactionDescriptor):
                reactions[name] = val
            elif isinstance(val, EmitterDescriptor):
                emitters[name] = val
            elif isinstance(val, (Action, Reaction)):  # pragma: no cover
                raise RuntimeError('Class methods can only be made actions or '
                                   'reactions using the corresponding decorators '
                                   '(%r)' % name)
        # Cache names
        cls.__attributes__ = [name for name in sorted(attributes.keys())]
        cls.__properties__ = [name for name in sorted(properties.keys())]
        cls.__actions__ = [name for name in sorted(actions.keys())]
        cls.__emitters__ = [name for name in sorted(emitters.keys())]
        cls.__reactions__ = [name for name in sorted(reactions.keys())]


class Component(with_metaclass(ComponentMeta, object)):
    """ The base component class.

    Components have attributes to represent static values, properties
    to represent state, actions that can mutate properties, and
    reactions that react to events such as property changes.

    Initial values of properties can be provided by passing them
    as keyword arguments.

    Subclasses can use :class:`Property <flexx.event.Property>` (or one
    of its subclasses) to define properties, and the
    :func:`action <flexx.event.action>`, :func:`reaction <flexx.event.reaction>`,
    and :func:`emitter <flexx.event.emitter>` decorators to create actions,
    reactions. and emitters, respectively.

    .. code-block:: python

        class MyComponent(event.Component):

            foo = event.FloatProp(7, settable=True)
            spam = event.Attribute()

            @event.action
            def inrease_foo(self):
                self._mutate_foo(self.foo + 1)

            @event.reaction('foo')
            def on_foo(self, *events):
                print('foo was set to', self.foo)

            @event.reaction('bar')
            def on_bar(self, *events):
                for ev in events:
                    print('bar event was emitted')

            @event.emitter
            def bar(self, v):
                return dict(value=v)  # the event to emit

    """

    _IS_COMPONENT = True
    _COUNT = 0

    id = Attribute(doc='The string by which this component is identified.')

    def __init__(self, *init_args, **property_values):

        Component._COUNT += 1
        self._id = self.__class__.__name__ + str(Component._COUNT)
        self._disposed = False

        # Init some internal variables. Note that __reactions__ is a list of
        # reaction names for this class, and __handlers a dict of reactions
        # registered to events of this object.
        # The __pending_events makes that reactions that connect to this
        # component right after it initializes get the initial events.
        self.__handlers = {}
        self.__pending_events = []
        self.__anonymous_reactions = []
        self.__initial_mutation = False

        # Prepare handlers with event types that we know
        for name in self.__emitters__:
            self.__handlers.setdefault(name, [])
        for name in self.__properties__:
            self.__handlers.setdefault(name, [])

        # With self as the active component (and thus mutatable), init the
        # values of all properties, and apply user-defined initialization
        with self:
            self._comp_init_property_values(property_values)
            self.init(*init_args)

        # Connect reactions and fire initial events
        self._comp_init_reactions()

    def __repr__(self):
        return "<Component '%s' at 0x%x>" % (self._id, id(self))

    def _comp_init_property_values(self, property_values):
        """ Initialize property values, combining given kwargs (in order)
        and default values.
        """
        values = []
        # First collect default property values (they come first)
        for name in self.__properties__:  # is sorted by name
            prop = getattr(self.__class__, name)
            setattr(self, '_' + name + '_value', prop._default)
            if name not in property_values:
                values.append((name, prop._default))
        # Then collect user-provided values
        for name, value in property_values.items():  # is sorted by occurance in py36
            if name not in self.__properties__:
                if name in self.__attributes__:
                    raise AttributeError('%s.%s is an attribute, not a property' %
                                         (self._id, name))
                else:
                    raise AttributeError('%s does not have property %s.' %
                                         (self._id, name))
            if callable(value):
                self._comp_make_implicit_setter(name, value)
                continue
            values.append((name, value))
        # Then process all property values
        self._comp_apply_property_values(values)

    def _comp_apply_property_values(self, values):
        """ Apply given property values, prefer using a setter, mutate otherwise.
        """
        self.__initial_mutation = True
        # First mutate all properties. Mutations validate input, but are always
        # independent.
        for name, value in values:
            self._mutate(name, value)
        # Now that all properties have a good initial value, invoke the setters
        # of properties that have one (and that is not auto-generated)
        for name, value in values:
            setter_name = ('_set' if name.startswith('_') else 'set_') + name
            setter = getattr(self, setter_name, None)
            if setter is not None:
                if getattr(setter, 'is_autogenerated', None) is False:
                    # This is an action, and one that the user wrote
                    setter(value)
        self.__initial_mutation = False

    def _comp_make_implicit_setter(self, prop_name, func):
        setter_func = getattr(self, 'set_' + prop_name, None)
        if setter_func is None:
            t = '%s does not have a set_%s() action for property %s.'
            raise TypeError(t % (self._id, prop_name, prop_name))
        setter_reaction = lambda: setter_func(func())
        reaction = Reaction(self, setter_reaction, 'auto', [])
        self.__anonymous_reactions.append(reaction)

    def _comp_init_reactions(self):
        """ Create our own reactions. These will immediately connect.
        """
        if self.__pending_events is not None:
            self.__pending_events.append(None)  # marker
            loop.call_soon(self._comp_stop_capturing_events)

        # Instantiate reactions by referencing them, Connections are resolved now.
        # Implicit (auto) reactions need to be invoked to initialize connections.
        for name in self.__reactions__:
            reaction = getattr(self, name)
            if reaction.get_mode() == 'auto':
                ev = Dict(source=self, type='', label='')
                loop.add_reaction_event(reaction, ev)
        # Also invoke the anonymouse auto-reactions
        for reaction in self.__anonymous_reactions:
            if reaction.get_mode() == 'auto':
                ev = Dict(source=self, type='', label='')
                loop.add_reaction_event(reaction, ev)

    def _comp_stop_capturing_events(self):
        """ Stop capturing events and flush the captured events.
        This gets scheduled to be called asap after initialization. But
        components created in our init() go first.
        """
        events = self.__pending_events
        self.__pending_events = None

        # The allow_reconnect stuff is to avoid reconnecting for properties
        # that we know did not change since the reaction connected.
        allow_reconnect = False
        for ev in events:
            if ev is None:
                allow_reconnect = True
                continue
            ev.allow_reconnect = allow_reconnect
            self.emit(ev.type, ev)

    def __enter__(self):
        loop._activate_component(self)
        loop.call_soon(self.__check_not_active)
        return self

    def __exit__(self, type, value, traceback):
        loop._deactivate_component(self)

    def __check_not_active(self):
        # Note: this adds overhead, especially during initialization, but it
        # is a valuable check ... it is something that could potentially be
        # disabled in "production mode".
        active_components = loop.get_active_components()
        if self in active_components:
            raise RuntimeError('It seems that the event loop is processing '
                               'events while a Component is active. This has a '
                               'high risk on race conditions.')

    def init(self):
        """ Initializer method. This method can be overloaded when
        creating a custom class. It is called with this component as a
        context manager (i.e. it is the active component), and it receives
        any positional arguments that were passed to the constructor.
        """
        pass

    def __del__(self):
        if not self._disposed:
            loop.call_soon(self._dispose)

    def dispose(self):
        """ Use this to dispose of the object to prevent memory leaks.
        Make all subscribed reactions forget about this object, clear
        all references to subscribed reactions, and disconnect all reactions
        defined on this object.
        """
        self._dispose()

    def _dispose(self):
        # Distinguish between private and public method to allow disposing
        # flexx.app.ProxyComponent without disposing its local version.

        self._disposed = True
        if not this_is_js():
            logger.debug('Disposing Component %r' % self)
        for name, reactions in self.__handlers.items():
            for i in range(len(reactions)):
                reactions[i][1]._clear_component_refs(self)
            while len(reactions):
                reactions.pop()  # no list.clear on legacy py
        for i in range(len(self.__reactions__)):
            getattr(self, self.__reactions__[i]).dispose()

    def _registered_reactions_hook(self):
        """ This method is called when the reactions change, can be overloaded
        in subclasses. The original method returns a list of event types for
        which there is at least one registered reaction. Overloaded methods
        should return this list too.
        """
        used_event_types = []
        for key, reactions in self.__handlers.items():
            if len(reactions) > 0:
                used_event_types.append(key)
        return used_event_types

    def _register_reaction(self, event_type, reaction, force=False):
        # Register a reaction for the given event type. The type
        # can include a label, e.g. 'pointer_down:foo'.
        # This is called from Reaction objects at initialization and when
        # they reconnect (dynamism).
        type, _, label = event_type.partition(':')
        label = label or reaction._name
        reactions = self.__handlers.get(type, None)
        if reactions is None:  # i.e. type not in self.__handlers
            reactions = []
            self.__handlers[type] = reactions
            if force:
                pass
            elif type.startswith('mouse_'):
                t = 'The event "{}" has been renamed to "pointer{}".'
                logger.warning(t.format(type, type[5:]))
            else:  # ! means force
                msg = ('Event type "{type}" does not exist on component {id}. ' +
                       'Use "!{type}" or "!xx.yy.{type}" to suppress this warning.')
                msg = msg.replace('{type}', type).replace('{id}', self._id)
                logger.warning(msg)

        # Insert reaction in good place (if not already in there) - sort as we add
        comp1 = label + '-' + reaction._id
        for i in range(len(reactions)):
            comp2 = reactions[i][0] + '-' + reactions[i][1]._id
            if comp1 < comp2:
                reactions.insert(i, (label, reaction))
                break
            elif comp1 == comp2:
                break  # already in there
        else:
            reactions.append((label, reaction))

        # Call hook to keep (subclasses of) the component up to date
        self._registered_reactions_hook()

    def disconnect(self, type, reaction=None):
        """ Disconnect reactions.

        Parameters:
            type (str): the type for which to disconnect any reactions.
                Can include the label to only disconnect reactions that
                were registered with that label.
            reaction (optional): the reaction object to disconnect. If given,
               only this reaction is removed.
        """
        # This is called from Reaction objects when they dispose and when
        # they reconnect (dynamism).
        type, _, label = type.partition(':')
        reactions = self.__handlers.get(type, ())
        for i in range(len(reactions)-1, -1, -1):
            entry = reactions[i]
            if not ((label and label != entry[0]) or
                    (reaction and reaction is not entry[1])):
                reactions.pop(i)
        self._registered_reactions_hook()

    def emit(self, type, info=None):
        """ Generate a new event and dispatch to all event reactions.

        Arguments:
            type (str): the type of the event. Should not include a label.
            info (dict): Optional. Additional information to attach to
                the event object. Note that the actual event is a Dict object
                that allows its elements to be accesses as attributes.
        """
        info = {} if info is None else info
        type, _, label = type.partition(':')
        if len(label):
            raise ValueError('The type given to emit() should not include a label.')
        # Prepare event
        if not isinstance(info, dict):
            raise TypeError('Info object (for %r) must be a dict, not %r' %
                            (type, info))
        ev = Dict(info)  # make copy and turn into nicer Dict on py
        ev.type = type
        ev.source = self
        # Push the event to the reactions (reactions use labels for dynamism)
        if self.__pending_events is not None:
            # Register pending reactions
            self.__pending_events.append(ev)
        else:
            # Reaction reconnections are applied directly; before a new event
            # occurs that the reaction might be subscribed to after the reconnect.
            reactions = self.__handlers.get(ev.type, ())
            for i in range(len(reactions)):
                label, reaction = reactions[i]
                if label.startswith('reconnect_'):
                    if getattr(ev, 'allow_reconnect', True) is True:
                        index = int(label.split('_')[1])
                        reaction.reconnect(index)
                else:
                    loop.add_reaction_event(reaction, ev)
        return ev

    def _mutate(self, prop_name, value, mutation='set', index=-1):
        """ Mutate a :class:`property <flexx.event.Property>`.
        Can only be called from an :class:`action <flexx.event.action>`.

        Each Component class will also have an auto-generated mutator function
        for each property: e.g. property ``foo`` can be mutated with
        ``c._mutate('foo', ..)`` or ``c._mutate_foo(..)``.

        Arguments:
            prop_name (str): the name of the property being mutated.
            value: the new value, or the partial value for partial mutations.
            mutation (str): the kind of mutation to apply. Default is 'set'.
               Partial mutations to list-like
               :class:`properties <flexx.event.Property>` can be applied by using
               'insert', 'remove', or 'replace'. If other than 'set', index must
               be specified, and >= 0. If 'remove', then value must be an int
               specifying the number of items to remove.
            index: the index at which to insert, remove or replace items. Must
                be an int for list properties.

        The 'replace' mutation also supports multidensional (numpy) arrays.
        In this case ``value`` can be an ndarray to patch the data with, and
        ``index`` a tuple of elements.
        """
        if not isinstance(prop_name, str):
            raise TypeError("_mutate's first arg must be str, not %s" %
                             prop_name.__class__)
        if prop_name not in self.__properties__:
            cname = self.__class__.__name__
            raise AttributeError('%s object has no property %r' % (cname, prop_name))

        if loop.can_mutate(self) is False:
            raise AttributeError('Trying to mutate property %s outside '
                                 'of an action or context.' % prop_name)

        # Prepare
        private_name = '_' + prop_name + '_value'
        validator_name = '_' + prop_name + '_validate'

        # Set / Emit
        old = getattr(self, private_name)

        if mutation == 'set':
            # Normal setting of a property
            value2 = getattr(self, validator_name)(value)
            setattr(self, private_name, value2)
            # Emit?
            if this_is_js():  # pragma: no cover
                is_equal = old == value2
            elif hasattr(old, 'dtype') and hasattr(value2, 'dtype'):  # pragma: no cover
                import numpy as np
                is_equal = np.array_equal(old, value2)
            else:
                is_equal = type(old) == type(value2) and old == value2
            if self.__initial_mutation is True:
                old = value2
                is_equal = False  # well, they are, but we want an event!
            if not is_equal:
                self.emit(prop_name,
                          dict(new_value=value2, old_value=old, mutation=mutation))
                return True
        else:
            # Array mutations - value is assumed to be a sequence, or int for 'remove'
            ev = Dict()
            ev.objects = value
            ev.mutation = mutation
            ev.index = index
            if isinstance(old, dict):
                if index != -1:
                    raise IndexError('For in-place dict mutations, '
                                     'the index is not used, and must be -1.')
                mutate_dict(old, ev)
            else:
                if index < 0:
                    raise IndexError('For insert, remove, and replace mutations, '
                                     'the index must be >= 0.')
                mutate_array(old, ev)
            self.emit(prop_name, ev)
            return True

    def get_event_types(self):
        """ Get the known event types for this component. Returns
        a list of event type names, for which there is a
        property/emitter or for which any reactions are registered.
        Sorted alphabetically. Intended mostly for debugging purposes.
        """
        types = list(self.__handlers)  # avoid using sorted (one less stdlib func)
        types.sort()
        return types

    def get_event_handlers(self, type):
        """ Get a list of reactions for the given event type. The order
        is the order in which events are handled: alphabetically by
        label. Intended mostly for debugging purposes.

        Parameters:
            type (str): the type of event to get reactions for. Should not
                include a label.

        """
        if not type:  # pragma: no cover - this is mostly since js allows missing args
            raise TypeError('get_event_handlers() missing "type" argument.')
        type, _, label = type.partition(':')
        if len(label):
            raise ValueError('The type given to get_event_handlers() '
                             'should not include a label.')
        reactions = self.__handlers.get(type, ())
        return [h[1] for h in reactions]

    def reaction(self, *connection_strings):
        """ Create a reaction by connecting a function to one or more events of
        this instance. Can also be used as a decorator. See the
        :func:`reaction <flexx.event.reaction>` decorator, and the intro
        docs for more information.
        """
        mode = 'normal'
        if (not connection_strings) or (len(connection_strings) == 1 and
                                        callable(connection_strings[0])):
            raise RuntimeError('Component.reaction() '
                                'needs one or more connection strings.')

        func = None
        if callable(connection_strings[0]):
            func = connection_strings[0]
            connection_strings = connection_strings[1:]
        elif callable(connection_strings[-1]):
            func = connection_strings[-1]
            connection_strings = connection_strings[:-1]

        for s in connection_strings:
            if not (isinstance(s, str) and len(s) > 0):
                raise ValueError('Connection string must be nonempty string.')

        def _react(func):
            if not callable(func):  # pragma: no cover
                raise TypeError('Component.reaction() decorator requires a callable.')
            if looks_like_method(func):
                return ReactionDescriptor(func, mode, connection_strings, self)
            else:
                return Reaction(self, func, mode, connection_strings)

        if func is not None:
            return _react(func)
        else:
            return _react


def mutate_dict(d, ev):
    """ Function to mutate an dict property in-place.
    Used by Component. The ``ev`` must be a dict with elements:

    * mutation: 'set', 'insert', 'remove' or 'replace'.
    * objects: the dict to set/insert/replace, or a list if keys to remove.
    * index: not used.
    """
    mutation = ev['mutation']
    objects = ev['objects']

    if mutation == 'set':
        d.clear()
    elif mutation in ('set', 'insert', 'replace'):
        assert isinstance(objects, dict)
        for key, val in objects.items():
            d[key] = val
    elif mutation == 'remove':
        assert isinstance(objects, (tuple, list))
        for key in objects:
            d.pop(key)
    else:
        raise NotImplementedError(mutation)


def _mutate_array_py(array, ev):
    """ Function to mutate a list- or array-like property in-place.
    Used by Component. The ``ev`` must be a dict with elements:

    * mutation: 'set', 'insert', 'remove' or 'replace'.
    * objects: the values to set/insert/replace, or the number of iterms to remove.
    * index: the (non-negative) index to insert/replace/remove at.
    """
    is_nd = hasattr(array, 'shape') and hasattr(array, 'dtype')
    mutation = ev['mutation']
    index = ev['index']
    objects = ev['objects']

    if is_nd:
        if mutation == 'set':  # pragma: no cover
            raise NotImplementedError('Cannot set numpy array in-place')
        elif mutation in ('insert', 'remove'):  # pragma: no cover
            raise NotImplementedError('Cannot resize numpy arrays')
        elif mutation == 'replace':
            if isinstance(index, tuple):  # nd-replacement
                slices = tuple(slice(index[i], index[i] + objects.shape[i], 1)
                               for i in range(len(index)))
                array[slices] = objects
            else:
                array[index:index+len(objects)] = objects
    else:
        if mutation == 'set':
            array[:] = objects
        elif mutation == 'insert':
            array[index:index] = objects
        elif mutation == 'remove':
            assert isinstance(objects, int)  # objects must be a count in this case
            array[index:index+objects] = []
        elif mutation == 'replace':
            array[index:index+len(objects)] = objects
        else:
            raise NotImplementedError(mutation)


def _mutate_array_js(array, ev):  # pragma: no cover
    """ Logic to mutate an list-like or array-like property in-place, in JS.
    """
    is_nd = hasattr(array, 'shape') and hasattr(array, 'dtype')
    mutation = ev.mutation
    index = ev.index
    objects = ev.objects

    if is_nd is True:
        if mutation == 'set':
            raise NotImplementedError('Cannot set nd array in-place')
        elif mutation in ('extend', 'insert', 'remove'):
            raise NotImplementedError('Cannot resize nd arrays')
        elif mutation == 'replace':
            raise NotImplementedError('Cannot replace items in nd array')
    else:
        if mutation == 'remove':
            assert isinstance(objects, float)  # objects must be a count in this case
        elif not isinstance(objects, list):
            raise TypeError('Inplace list/array mutating requires a list of objects.')
        if mutation == 'set':
            array.splice(0, len(array), *objects)
        elif mutation == 'insert':
            array.splice(index, 0, *objects)
        elif mutation == 'remove':
            array.splice(index, objects)
        elif mutation == 'replace':
            array.splice(index, len(objects), *objects)
        else:
            raise NotImplementedError(mutation)


mutate_array = _mutate_array_py
_mutate_dict_js = _mutate_dict_py = mutate_dict
