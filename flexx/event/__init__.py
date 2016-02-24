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

Emitter
-------

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
    
    ob = @event.HasEvents()
    
    @event.connect('ob.foo')
    def handle_foo(*events):
        print(events)
    
    ob.emit('foo', dict(value=42))  # will invoke handle_foo()

We can see a few things from this example. Firstly, the handler is
connected via a *connection-string* that a path to the event. In this
case, 'ob.foo' means it connects to the event-type 'foo' of the object
'ob'. This connection-string can be longer, e.g.
'path.to.an.emitter.event_type:label'. We cover labels further below.
We also discuss some powerful mechanics related to connection-strings
when we cover dynamism.

We can also see that the handler function accepts ``*events`` argument.
This is because handlers can be passed zero or more events. If a function
is called manually (e.g. ``ob.handle_foo()``) it will have zero events.
When called by the event system, it will have at least 1 event. The handler
function is called in a next iteration of the event loop. If multiple
events are emitted for this handler, the handler function is called
just once. It is up to the programmer to determine whether all events
need some form of processing, or if only one action is required. In
general this is more efficient than having the handler function called
each time that the event is emitted.

Another feature of this system, is that a handler can connect to multiple
events:

.. code-block:: python
    
    ob = event.HasEvents()
    
    @event.connect('ob.foo', 'ob.bar')
    def handle_foo_and_bar(*events):
        ...

The recommended way to write apps is to write handlers as part of
an HasEvents subclass:

.. code-block:: python

    class MyObject(event.HasEvents):
       
        @event.connect('foo')
        def _handle_foo(self, **events):
            ...


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


Naming in the context of events
-------------------------------

* event: something that has occurred, represented by an event object (a Dict)
* event emitter: an object that can emit events, of a class that
  inherits from HasEvents.
* handler: an object that can handle events, it wraps a handler function.
* connection: generic term to indicate a connection between a handler
  and an emitter.
* connection-string: a string used to connect a handler to an emitter.
  E.g. 'path.to.emitter.event_type:label'.
* type: a string name indicating the type of event, e.g. 'mouse_down'.
  When type is an argument to a function, the label can also be included,
  e.g. 'mouse_down:foo'.
* label: a string name that can be specified for a connection. It can
  be used to influence the order of event handling, to disconnect handlers,
  and to help identify the source of an event inside a handler.

"""

from ._dict import Dict
from ._handler import connect, loop
from ._properties import prop, readonly, emitter
from ._hasevents import HasEvents

from ._hasevents import new_type, with_metaclass
