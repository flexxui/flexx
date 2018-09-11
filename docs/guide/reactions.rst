---------
React
---------

:func:`Reactions <flexx.event.reaction>` are used to react to events and
changes in properties, using an underlying handler function:


.. code-block:: python

    class MyObject(event.Component):

        first_name = event.StringProp(settable=True)
        last_name = event.StringProp(settable=True)

        @event.reaction('first_name', 'last_name')
        def greet(self, *events):
            print('hi', self.first_name, self.last_name)

        @event.reaction('!foo')
        def handle_foo(self, *events):
            for ev in events:
                print(ev)


This example demonstrates multiple concepts. Firstly, the reactions are
connected via *connection-strings* that specify the types of the
event; in this case the ``greeter`` reaction is connected to "first_name" and
"last_name", and ``handle_foo`` is connected to the event-type "foo" of the
object. This connection-string can also be a path, e.g.
"sub.subsub.event_type". This allows for some powerful mechanics, as
discussed in the section on dynamism.

One can also see that the reaction-function accepts ``*events`` argument.
This is because reactions can be passed zero or more events. If a reaction
is called manually (e.g. ``ob.handle_foo()``) it will have zero events.
When called by the event system, it will have at least 1 event. When
e.g. a property is set twice, the function will be called
just once, but with multiple events. If all events need to be processed
individually, use ``for ev in events: ...``.

In most cases, you will connect to events that are known beforehand,
like those corresponding to properties and emitters.
If you connect to an event that is not known (like "foo" in the example
above) Flexx will display a warning. Use ``'!foo'`` as a connection string
(i.e. prepend an exclamation mark) to suppress such warnings.

Another useful feature of the event system is that a reaction can connect to
multiple events at once, as the ``greet`` reaction does.

The following is less common, but it is possible to create a reaction from a
normal function, by using the
:func:`Component.reacion() <flexx.event.Component.reaction>` method:

.. code-block:: python

    c = MyComponent()

    # Using a decorator
    @c.reaction('foo', 'bar')
    def handle_func1(self, *events):
        print(events)

    # Explicit notation
    def handle_func2(self, *events):
        print(events)
    c.reaction(handle_func2, 'foo', 'bar')
    # this is fine too: c.reaction('foo', 'bar', handle_func2)


Greedy and automatic reactions
==============================

Each reaction operates in a certain "mode". In mode "normal", the event system
ensures that all events are handled in the order that they were emitted. This
is often the most useful approach, but this implies that a reaction can be
called multiple times during a single event loop iteration, with other
reactions called in between to ensure the consisten event order.

If it is preferred that all events targeted at a reaction are handled with
a single call to that reaction, it can be set to mode "greedy". Cases where
this makes sense is when all related events must be processed simultenously,
or simply when performance matters a lot and order matters less.

Reactions with mode "auto" are automatically triggered when any of the
properties that the reaction uses is changed. Such reactions can be
created by specifying the ``mode`` argument, or simply by creating a
reaction with zero connections strings. We refer to such reactions as
"auto reactions" or "implicit reactions". This is a convenient feature,
but should probably be avoided when a lot (say hundreds) of properties
are accessed.

.. code-block:: python

    class MyObject(event.Component):

        first_name = event.StringProp(settable=True)
        last_name = event.StringProp(settable=True)

        @event.reaction
        def greet(self):
            print('hi', self.first_name, self.last_name)

A similar useful feature is to assign a property (at initialization) using a
function. In such a case, the function is turned into an implicit reaction.
This can be convenient to easily connect different parts of an app.

.. code-block:: python

    class MyObject(event.Component):

        first_name = event.StringProp(settable=True)
        last_name = event.StringProp(settable=True)

    person = MyObject()
    label = UiLabel(text=lambda: person.first_name)


Reacting to in-place mutations
==============================

In-place mutations to lists or arrays can be reacted to by processing
the events one by one:

.. code-block:: python

    class MyComponent(event.Component):

        @event.reaction('other.items')
        def track_array(self, *events):
            for ev in events:
                if ev.mutation == 'set':
                    self.items[:] = ev.objects
                elif ev.mutation == 'insert':
                    self.items[ev.index:ev.index] = ev.objects
                elif ev.mutation == 'remove':
                    self.items[ev.index:ev.index+ev.objects] = []  # objects is int here
                elif ev.mutation == 'replace':
                    self.items[ev.index:ev.index+len(ev.objects)] = ev.objects
                else:
                    assert False, 'we cover all mutations'

For convenience, the mutation can also be "replicated" using the
``flexx.event.mutate_array()`` and ``flexx.event.mutate_dict()`` functions.


Labels
======

Labels are a feature that makes it possible to infuence the order by
which reactions are called, and provide a means to disconnect
specific (groups of) handlers.

.. code-block:: python

    class MyObject(event.Component):

        @event.reaction('foo')
        def given_foo_handler(*events):
                ...

        @event.reaction('foo:aa')
        def my_foo_handler(*events):
            # This one is called first: 'aa' < 'given_f...'
            ...

When an event is emitted, any connected reactions are scheduled in the
order of a key, which is the label if present, and
otherwise the name of the name of the reaction.

The label can also be used in the
:func:`disconnect() <flexx.event.Component.disconnect>` method:

.. code-block:: python

    @h.reaction('foo:mylabel')
    def handle_foo(*events):
        ...

    ...

    h.disconnect('foo:mylabel')  # don't need reference to handle_foo


Dynamism
========

Dynamism is a concept that allows one to connect to events for which
the source can change. For the following example, assume that ``Node``
is a ``Component`` subclass that has properties ``parent`` and
``children``.

.. code-block:: python

    main = Node()
    main.parent = Node()
    main.children = Node(), Node()

    @main.reaction('parent.foo')
    def parent_foo_handler(*events):
        ...

    @main.reaction('children*.foo')
    def children_foo_handler(*events):
        ...

The ``parent_foo_handler`` gets invoked when the "foo" event gets
emitted on the parent of main. Similarly, the ``children_foo_handler``
gets invoked when any of the children emits its "foo" event. Note that
in some cases you might also want to connect to changes of the ``parent``
or ``children`` property itself.

The event system automatically reconnects reactions when necessary. This
concept makes it very easy to connect to the right events without the
need for a lot of boilerplate code.

Note that the above example would also work if ``parent`` would be a
regular attribute instead of a property, but the reaction would not be
automatically reconnected when it changed.


Implicit dynamism
=================

Implicit reactions are also dynamic, maybe even more so! In the example below,
the reaction accesses the ``children`` property, thus it will be called whenever
that property changes. It also connects to the ``visible`` event of
all children, and to the ``foo`` event of all children that are visible.

.. code-block:: python

   @main.reaction
    def _implicit_reacion():
        for child in main.children:
            if child.visible:
                do_something_with(child.foo)

This mechanism is powerful, but one can see how it can potentially
access (and thus connect to) many properties, especially if the reaction
calls other functions that access more properties. Also keep in mind that
implicit reactions have more overhead (because they fully reconnect
every time after they are called). One should probably avoid them for
properties that change 100 times per second.
