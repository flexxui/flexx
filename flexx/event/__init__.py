"""
The event module provides an simple event framework as well as a
property system (and properties send events when they get changed).
Together, these provide a simple yet powerful means to make different
components of an application react to each-other and to user input.

Event
-----

An event is something that has occurred, at a certain moment in time.
Like a mouse pressed down or moved, or a property changing its value.
In this framework, events are represented with dictionary objects that
provide information about the event. We use a custom `Dict` class that
inherits from `dict` but allows attribute access, e.g. ``ev.button`` as
an alternative to ``ev['button']``.

The HasEvents class
-------------------

The HasEvents class provides a base class for objects that need to
have properties and/or emit events. E.g. a ``flexx.ui.Widget`` inherits from
``flexx.app.Model``, which inherits from ``flexx.event.HasEvents``.

Events are emitted using the ``emitter.emit()`` method, which accepts a
name for the type of the event, and a dict: e.g. 
``emitter.emit('mouse_down', dict(button=1, x=103, y=211))``.

As a user, you generally do not need to emit events in this way, but it
happens implicitly, e.g. when setting a property, as we'll see below.

Handler
-------

A handler is an object that can handle events. It wraps a function. Handlers
can be created using the ``connect`` decorator:

.. code-block:: python

    class MyObject(event.HasEvents):
       
        @event.connect('foo')
        def handle_foo(self, *events):
            print(events)
    
    ob = MyObject()
    ob.emit('foo', dict(value=42))  # will invoke handle_foo()

We can see a few things from this example. Firstly, the handler is
connected via a *connection-string* that a path to the event. In this
case, 'foo' means it connects to the event-type 'foo' of the object'.
This connection-string can be longer, e.g. 'sub.subsub.event_type:label'.
We cover labels further below. We also discuss some powerful mechanics
related to connection-strings when we cover dynamism.

We can also see that the handler function accepts ``*events`` argument.
This is because handlers can be passed zero or more events. If a function
is called manually (e.g. ``ob.handle_foo()``) it will have zero events.
When called by the event system, it will have at least 1 event. The handler
function is called in a next iteration of the event loop. If multiple
events are emitted in a row, the handler function is called
just once, but with multiple events. It is up to the programmer to
determine whether all events need some form of processing, or if only
one action is required. In general this is more efficient than having
the handler function called each time that the event is emitted.

Another feature of this system is that a handler can connect to multiple
events:

.. code-block:: python

    class MyObject(event.HasEvents):
       
        @event.connect('foo', 'bar')
        def handle_foo_and_bar(self, *events):
            print(events)

Handlers do not have to be part of the subclass:

.. code-block:: python

    h = HasEvents()
    
    # Using a decorator
    @h.connect('foo', 'bar')
    def handle_func1(self, *events):
        print(events)
    
    # Explicit notation
    def handle_func2(self, *events):
        print(events)
    h.connect(handle_func2, 'foo', 'bar')


Event generators
----------------

Apart from using ``emit()`` there are certain attributes of ``HasEvents``
that help generate events or generate events automatically.

Properties
==========

Properties can be created like this:

.. code-block:: python

    class MyObject(event.HasEvents):
       
        @event.prop
        def foo(self, v=0):
            ''' This is a float indicating bla.
            '''
            return float(v)

The function that is decorated should have one argument (the new value
for the property), and it should have a default value. The function body
is used to validate and normalize the provided input. In this case we
just (try to) cast whatever input is given to a float. The docstring
of the function will be the docstring of the property (and ends up
correctly in Sphynx docs).


Readonly
========

A readonly is a property that can only be read. It can be set internally
using ``HasEvents._set_prop()``.

.. code-block:: python

    class MyObject(event.HasEvents):
       
        @event.readonly
        def foo(self, v=0):
            ''' This is a float indicating bla.
            '''
            return float(v)
        
        def _somewhere(self):
            self._set_prop('foo', 42)

Event
=====

Uuuhm... the name is awkward. Emitter? But we also have that already.

.. code-block:: python

    class MyObject(event.HasEvents):
    
        @event.event
        def mouse_down(self, js_event):
            ''' Yay, users can read in the docs that this event exists, and
            when it occurs!
            '''
            return dict(button=js_event.button)


Labels
------

TODO

Dynamism
--------

TODO

Patterns
--------

TODO

* signaling (most common)
* pub sub
* overloadable event handlers as in Qt
* observer pattern
* send events into an object without caring what event it can handle (ala PhosphorJS)

"""

from ._dict import Dict
from ._handler import connect, loop
from ._emitters import prop, readonly, emitter
from ._hasevents import HasEvents

# from ._hasevents import new_type, with_metaclass
