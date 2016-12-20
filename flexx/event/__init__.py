"""
The event module provides a simple system for properties and events,
to let different components of an application react to each-other and
to user input.

In short:

* The :class:`HasEvents <flexx.event.HasEvents>` class provides objects
  that have properties and can emit events.
* There are three decorators to create :func:`properties <flexx.event.prop>`,
  :func:`readonlies <flexx.event.readonly>` and 
  :func:`emitters <flexx.event.emitter>`.
* There is a decorator to :func:`connect <flexx.event.connect>` a method
  to an event.


Event
-----

An event is something that has occurred at a certain moment in time,
such as the mouse being pressed down or a property changing its value.
In this framework events are represented with dictionary objects that
provide information about the event (such as what button was pressed,
or the old and new value of a property). A custom :class:`Dict <flexx.event.Dict>`
class is used that inherits from ``dict`` but allows attribute access,
e.g. ``ev.button`` as an alternative to ``ev['button']``.


The HasEvents class
-------------------

The :class:`HasEvents <flexx.event.HasEvents>` class provides a base
class for objects that have properties and/or emit events. E.g. a
``flexx.ui.Widget`` inherits from ``flexx.app.Model``, which inherits
from ``flexx.event.HasEvents``.

Events are emitted using the :func:`emit() <flexx.event.HasEvents.emit>`
method, which accepts a name for the type of the event, and optionally a dict,
e.g. ``emitter.emit('mouse_down', dict(button=1, x=103, y=211))``.

The HasEvents object will add two attributes to the event: ``source``,
a reference to the HasEvents object itself, and ``type``, a string
indicating the type of the event.

As a user, you generally do not need to emit events explicitly; events are
automatically emitted, e.g. when setting a property.


Handler
-------

A handler is an object that can handle events. Handlers can be created
using the :func:`connect <flexx.event.connect>` decorator:

.. code-block:: python
    
    from flexx import event
    
    class MyObject(event.HasEvents):
       
        @event.connect('foo')
        def handle_foo(self, *events):
            print(events)
    
    ob = MyObject()
    ob.emit('foo', dict(value=42))  # will invoke handle_foo()

This example demonstrates a few concepts. Firstly, the handler is
connected via a *connection-string* that specifies the type of the
event; in this case the handler is connected to the event-type "foo"
of the object. This connection-string can also be a path, e.g.
"sub.subsub.event_type". This allows for some powerful mechanics, as
discussed in the section on dynamism.

One can also see that the handler function accepts ``*events`` argument.
This is because handlers can be passed zero or more events. If a handler
is called manually (e.g. ``ob.handle_foo()``) it will have zero events.
When called by the event system, it will have at least 1 event. When
e.g. a property is set twice, the handler function is called
just once, with multiple events, in the next event loop iteration. It
is up to the programmer to determine whether only one action is
required, or whether all events need processing. In the latter case,
just use ``for ev in events: ...``.

In most cases, you will connect to events that are known beforehand,
like those they correspond to properties, readonlies and emitters. 
If you connect to an event that is not known (as in the example above)
it might be a typo and Flexx will display a warning. Use `'!foo'` as a
connection string (i.e. prepend an exclamation mark) to suppress such
warnings.

Another useful feature of the event system is that a handler can connect to
multiple events at once:

.. code-block:: python

    class MyObject(event.HasEvents):
       
        @event.connect('foo', 'bar')
        def handle_foo_and_bar(self, *events):
            print(events)

To create a handler from a normal function, use the
:func:`HasEvents.connect() <flexx.event.HasEvents.connect>` method:

.. code-block:: python

    h = event.HasEvents()
    
    # Using a decorator
    @h.connect('foo', 'bar')
    def handle_func1(self, *events):
        print(events)
    
    # Explicit notation
    def handle_func2(self, *events):
        print(events)
    h.connect(handle_func2, 'foo', 'bar')


Event emitters
--------------

Apart from using :func:`emit() <flexx.event.HasEvents.emit>` there are
certain attributes of ``HasEvents`` instances that generate events.

Properties
==========

Settable properties can be created easiliy using the
:func:`prop <flexx.event.prop>` decorator:

.. code-block:: python

    class MyObject(event.HasEvents):
       
        @event.prop
        def foo(self, v=0):
            ''' This is a float indicating bla bla ...
            '''
            return float(v)

The function that is decorated is essentially the setter function, and
should have one argument (the new value for the property), which can
have a default value (representing the initial value). The function
body is used to validate and normalize the provided input. In this case
the input is simply cast to a float. The docstring of the function will
be the docstring of the property (e.g. for Sphynx docs).

An alternative initial value for a property can be provided upon instantiation:

.. code-block:: python

    m = MyObject(foo=3)

Readonly
========

Readonly properties are created with the 
:func:`readonly <flexx.event.readonly>` decorator. The value of a
readonly property can be set internally using the
:func:`_set_prop() <flexx.event.HasEvents._set_prop>` method:.

.. code-block:: python

    class MyObject(event.HasEvents):
       
        @event.readonly
        def foo(self, v=0):
            ''' This is a float indicating bla.
            '''
            return float(v)
        
        def _somewhere(self):
            self._set_prop('foo', 42)

Emitter
=======

Emitter attributes make it easy to generate events, and function as a
placeholder to document events on a class. They are created with the
:func:`emitter <flexx.event.emitter>` decorator.

.. code-block:: python

    class MyObject(event.HasEvents):
    
        @event.emitter
        def mouse_down(self, js_event):
            ''' Event emitted when the mouse is pressed down.
            '''
            return dict(button=js_event.button)

Emitters can have any number of arguments and should return a dictionary,
which will get emitted as an event, with the event type matching the name
of the emitter.


Connection string syntax
------------------------

The strings used to connect events follow a few simple syntax rules:

* Connection strings consist of parts separated by dots, thus forming a path.
  If an element on the path is a property, the connection will automatically
  reset when that property changes (a.k.a. dynamism, more on this below).
* Each part can end with one star ('*'), indicating that the part is a list
  and that a connection should be made for each item in the list. 
* With two stars, the connection is made *recursively*, e.g. "children**"
  connects to "children" and the children's children, etc.
* Stripped of '*', each part must be a valid identifier (ASCII).
* The total string optionally has a label suffix separated by a colon. The
  label itself may consist of any chars.
* The string can have a "!" at the very start to suppress warnings for
  connections to event types that Flexx is not aware of at initialization
  time (i.e. not corresponding to a property or emitter).

An extreme example could be ``"!foo.children**.text:mylabel"``, which connects
to the "text" event of the children (and their children, and their children's
children etc.) of the ``foo`` attribute. The "!" is common in cases like
this to suppress warnings if not all children have a ``text`` event/property.

Labels
======

Labels are a feature that makes it possible to infuence the order by
which event handlers are called, and provide a means to disconnect
specific (groups of) handlers. The label is part of the connection
string: 'foo.bar:label'.

.. code-block:: python
    
    class MyObject(event.HasEvents):
    
        @event.connect('foo')
        def given_foo_handler(*events):
                ...
        
        @event.connect('foo:aa')
        def my_foo_handler(*events):
            # This one is called first: 'aa' < 'given_f...'
            ...

When an event is emitted, the event is added to the pending events of
the handlers in the order of a key, which is the label if present, and
otherwise the name of the handler. Note that this does not guarantee
the order in case a handler has multiple connections: a handler can be
scheduled to handle its events due to another event, and a handler
always handles all its pending events at once.

The label can also be used in the
:func:`disconnect() <flexx.event.HasEvents.disconnect>` method:

.. code-block:: python

    @h.connect('foo:mylabel')
    def handle_foo(*events):
        ...
    
    ...
    
    h.disconnect('foo:mylabel')  # don't need reference to handle_foo


Dynamism
========

Dynamism is a concept that allows one to connect to events for which
the source can change. For the following example, assume that ``Node``
is a ``HasEvents`` subclass that has properties ``parent`` and
``children``.

.. code-block:: python
    
    main = Node()
    main.parent = Node()
    main.children = Node(), Node()
    
    @main.connect('parent.foo')
    def parent_foo_handler(*events):
        ...
    
    @main.connect('children*.foo')
    def children_foo_handler(*events):
        ...

The ``parent_foo_handler`` gets invoked when the "foo" event gets
emitted on the parent of main. Similarly, the ``children_foo_handler``
gets invoked when any of the children emits its "foo" event. Note that
in some cases you might also want to connect to changes of the ``parent``
or ``children`` property itself.

The event system automatically reconnects handlers when necessary. This
concept makes it very easy to connect to the right events without the
need for a lot of boilerplate code.

Note that the above example would also work if ``parent`` would be a
regular attribute instead of a property, but the handler would not be
automatically reconnected when it changed.


Patterns
--------

This event system is quite flexible and designed to cover the needs
of a variety of event/messaging mechanisms. This section discusses
how this system relates to some common patterns, and how these can be
implemented.

Observer pattern
================

The idea of the observer pattern is that observers keep track (the state
of) of an object, and that object is agnostic about what it's tracked by.
For example, in a music player, instead of writing code to update the
window-title inside the function that starts a song, there would be a
concept of a "current song", and the window would listen for changes to
the current song to update the title when it changes.

In ``flexx.event``, a ``HasEvents`` object keeps track of its observers
(handlers) and notifies them when there are changes. In our music player
example, there would be a property "current_song", and a handler to
take action when it changes.

As is common in the observer pattern, the handlers keep track of the
handlers that they observe. Therefore both handlers and ``HasEvents``
objects have a ``dispose()`` method for cleaning up.

Signals and slots
=================

The Qt GUI toolkit makes use of a mechanism called "signals and slots" as
an easy way to connect different components of an application. In
``flexx.event`` signals translate to readonly properties, and slots to
the handlers that connect to them.

Overloadable event handlers
===========================

In Qt, the "event system" consists of methods that handles an event, which
can be overloaded in subclasses to handle an event differently. In
``flexx.event``, handlers can similarly be re-implemented in subclasses,
and these can call the original handler using ``super()`` if needed.

Publish-subscribe pattern
==========================

In pub-sub, publishers generate messages identified by a 'topic', and
subscribers can subscribe to such topics. There can be zero or more publishers
and zero or more subscribers to any topic. 

In ``flexx.event`` a `HasEvents` object can play the role of a broker.
Publishers can simply emit events. The event type represents the message
topic. Subscribers are represented by handlers.

"""

import logging
logger = logging.getLogger(__name__)
del logging

# flake8: noqa
from ._dict import Dict
from ._loop import loop
from ._handler import Handler, connect
from ._emitters import prop, readonly, emitter
from ._hasevents import HasEvents

# from ._hasevents import new_type, with_metaclass
