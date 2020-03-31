---------
Reactions
---------

:func:`Reactions <flexx.event.reaction>` are used to react to events and
changes in properties, using an underlying handler function:


.. UIExample:: 100

    from flexx import flx

    class Example(flx.Widget):

        def init(self):
            super().init()
            with flx.VBox():
                with flx.HBox():
                    self.firstname = flx.LineEdit(placeholder_text='First name')
                    self.lastname = flx.LineEdit(placeholder_text='Last name')
                with flx.HBox():
                    self.but = flx.Button(text='Reset')
                    self.label = flx.Label(flex=1)

        @flx.reaction('firstname.text', 'lastname.text')
        def greet(self, *events):
            self.label.set_text('hi ' + self.firstname.text + ' ' + self.lastname.text)

        @flx.reaction('but.pointer_click')
        def reset(self, *events):
            self.label.set_text('')


This example demonstrates multiple concepts. Firstly, the reactions are
connected via *connection-strings* that specify the types of the event;
in this case the ``greet()`` reaction is connected to "firstname.text"
and "lastname.text", and ``reset()`` is connected to the event-type
"pointer_click" event of the button. One can see how the
connection-string is a path, e.g. "sub.subsub.event_type". This allows
for some powerful mechanics, as discussed in the section on dynamism.

One can also see that the reaction-function accepts ``*events`` argument.
This is because reactions can be passed zero or more events. If a reaction
is called manually (e.g. ``ob.handle_foo()``) it will have zero events.
When called by the event system, it will have at least 1 event. When
e.g. a property is set twice, the function will be called
just once, but with multiple events. If all events need to be processed
individually, use:

.. code-block:: python

    @flx.reaction('foo')
    def handler(self, *events):
        for ev in events:
            ...

In most cases, you will connect to events that are known beforehand,
like those corresponding to properties and emitters.
If you connect to an event that is not known Flexx will display a warning.
Prepend an exclamation mark (e.g. ``'!foo'``) to suppress such warnings.


Greedy and automatic reactions
------------------------------

Each reaction operates in a certain "mode". In mode "normal" (the
default), the event system ensures that all events are handled in the
order that they were emitted. This is often the most sensible approach,
but this implies that a reaction can be called multiple times during a
single event loop iteration, with other reactions called in between to
ensure the consistent event order.

If it is preferred that all events targeted at a reaction are handled with
a single call to that reaction, it can be set to mode "greedy". Cases where
this makes sense is when all related events must be processed simultaneously,
or simply when performance matters a lot and order matters less.

.. code-block:: python

    @flx.reaction('foo', mode='greedy')
    def handler(self, *events):
        ...

Reactions with mode "auto" are automatically triggered when any of the
properties that the reaction uses is changed. Such reactions can be
created by specifying the ``mode`` argument, or simply by creating a
reaction with zero connections strings. We refer to such reactions as
"auto reactions" or "implicit reactions".

This is a very convenient feature, but it has more overhead than a
normal reaction, and should therefore probably be avoided when a lot
of properties are accessed, or when the used properties change very
often. It's hard to tell exactly when it starts to significantly hurt
performance, but "often" is probably around hundreds and "often around
100 times per second. Just keep this in mind and do your own benchmarks
when needed.

.. UIExample:: 100

    from flexx import flx

    class Example(flx.Widget):

        def init(self):
            super().init()
            with flx.VBox():
                with flx.HBox():
                    self.slider1 = flx.Slider(flex=1)
                    self.slider2 = flx.Slider(flex=1)
                self.label = flx.Label(flex=1)

        @flx.reaction
        def slders_combined(self):
            self.label.set_text('{:.2f}'.format(self.slider1.value + self.slider2.value))

A similar useful feature is to assign a property (at initialization) using a
function. In such a case, the function is turned into an implicit reaction.
This can be convenient to easily connect different parts of an app.

.. UIExample:: 100

    from flexx import flx

    class Example(flx.Widget):

        def init(self):
            super().init()
            with flx.VBox():
                with flx.HBox():
                    self.slider1 = flx.Slider(flex=1)
                    self.slider2 = flx.Slider(flex=1)
                self.label = flx.Label(flex=1, text=lambda:'{:.2f}'.format(self.slider1.value * self.slider2.value))


Reacting to in-place mutations
------------------------------

In-place mutations to lists or arrays can be reacted to by processing
the events one by one:

.. code-block:: python

    class MyComponent(flx.Component):

        @flx.reaction('other.items')
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
``flx.mutate_array()`` and ``flx.mutate_dict()`` functions.


Connection string labels
------------------------

Connection strings can have labels to infuence the order by
which reactions are called, and provide a means to disconnect
specific (groups of) handlers at once.

.. code-block:: python

    class MyObject(flx.Component):

        @flx.reaction('foo')
        def given_foo_handler(*events):
                ...

        @flx.reaction('foo:aa')
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
--------

Dynamism is a concept that allows one to connect to events for which
the source can change. In the example below, we connect to the click event
of a list of buttons, which keeps working even as that list changes.

.. UIExample:: 150

    from flexx import flx

    class Example(flx.Widget):

        def init(self):
            super().init()
            with flx.VBox():
                with flx.HBox():
                    self.but = flx.Button(text='add')
                    self.label = flx.Label(flex=1)
                with flx.HBox() as self.box:
                    flx.Button(text='x')

        @flx.reaction('but.pointer_click')
        def add_widget(self, *events):
            flx.Button(parent=self.box, text='x')

        @flx.reaction('box.children*.pointer_click')
        def a_button_was_pressed(self, *events):
            ev = events[-1]  # only care about last event
            self.label.set_text(ev.source.id + ' was pressed')

The ``a_button_was_pressed`` gets invoked when any of the buttons inside
``box`` is clicked. When the box's children changes, the reaction is
automatically reconnected. Note that in some cases you might also want
to connect to changes of the ``box.children`` property itself.

The above works because ``box.children`` is a property. The reaction
would still work if it would connect to widgets in a regular list, but
it would not be dynamic.


Implicit dynamism
-----------------

Implicit reactions are also dynamic, maybe even more so! In the example below,
the reaction accesses the ``children`` property, thus it will be called whenever
that property changes. It also connects to the ``visible`` event of
all children, and to the ``foo`` event of all children that are visible.

.. UIExample:: 150

    from flexx import flx

    class Example(flx.Widget):

        def init(self):
            super().init()
            with flx.VBox():
                with flx.HBox():
                    self.but = flx.Button(text='add')
                    self.label = flx.Label(flex=1)
                with flx.HBox() as self.box:
                    flx.CheckBox()

        @flx.reaction('but.pointer_click')
        def add_widget(self, *events):
            flx.CheckBox(parent=self.box)

        @flx.reaction
        def a_button_was_pressed(self):
            ids = []
            for checkbox in self.box.children:
                if checkbox.checked:
                    ids.append(checkbox.id)
            self.label.set_text('checked: ' + ', '.join(ids))

This mechanism is powerful, but one can see how it can potentially
access (and thus connect to) many properties, especially if the reaction
calls other functions that access more properties. As mentioned before,
keep in mind that implicit reactions have more overhead, which scales with the
number of properties that are accessed.


Next
----

Next up: :doc:`PScript, modules and scope <pscript_modules_scope>`.
