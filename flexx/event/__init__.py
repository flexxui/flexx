"""
The event module provides an simple event framework as well as a
property system (and properties send events when they get changed).
Together, these provide a simple yet powerful means to make different
components of an application react to each-other and to user input.


Event
-----

An event is something that has occurred, at a certain moment in time,
such as a mouse pressed down or a property changing its value. In this
framework events are represented with dictionary objects that provide
information about the event. We use a custom `Dict` class that inherits
from `dict` but allows attribute access, e.g. ``ev.button`` as an
alternative to ``ev['button']``.


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

A handler is an object that can handle events. Handlers can be created
using the ``connect`` decorator:

.. code-block:: python

    class MyObject(event.HasEvents):
       
        @event.connect('foo')
        def handle_foo(self, *events):
            print(events)
    
    ob = MyObject()
    ob.emit('foo', dict(value=42))  # will invoke handle_foo()

We can see a few things from this example. Firstly, the handler is
connected via a *connection-string* that specifies the type of the
event; in this case the handler is connected to the event-type 'foo'
of the object. This connection-string can also be a path, e.g.
'sub.subsub.event_type:label'. We cover labels further below. We also
discuss some powerful mechanics related to connection-strings when we
cover dynamism.

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


Event emitters
--------------

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

An alternative initial value for a property can be provided upon instantiation:

.. code-block:: python

    m = MyObject(foo=3)

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

Emitter
=======

An emitter is an attribute that makes it easy to generate events. It also
functions as a placeholder to document events on a class.

.. code-block:: python

    class MyObject(event.HasEvents):
    
        @event.emitter
        def mouse_down(self, js_event):
            ''' Event emitted when the mouse is pressed down.
            '''
            return dict(button=js_event.button)


Labels
------

Labels are a feature that makes it possible to infuence the order by
which event handlers are called, and provide a means to identify events
inside a handler.

.. code-block:: python
    
    class MyObject(event.HasEvents):
    
        @event.connect('foo')
        def given_foo_handler(*events):
                ...
        
        @event.connect('foo:aa')
        def my_foo_handler(*events):
            # I want this one called first: 'aa' < 'given_f...'
            ...

When an event is emitted, the event is added to the pending events of
the handlers in the order of a key, which is the label if present, and
otherwise the name of the handler. Note that this does not guarantee
the order in case a handler has multiple connections: a handler can be
scheduled to handle its events due to another event, and a handler
always handles all its pending events at once.

.. code-block:: python
    
    class MyObject(event.HasEvents):
    
        @event.connect('foo:x', 'bar:y')
        def handler1(*events):
            for ev in events:
                if ev.label == 'x':
                ...

The label name is available as an attribute of the event. 
This example is a bit silly, because you could just as well look at ev.type.
An example with dynamism could make more sense. Or maybe having the label
on the event is a feature we should drop?


Dynamism
--------

TODO


Patterns
--------

This event system is quite flexible. It is designed to cover the needs
of a variety of event/messaging mechanisms. In this section we discuss
how this system relates to some common patterns, and how these can be
implemented.

Observer pattern
================

The idea of the observer pattern is that observers keep track (the state
of) of an object, and that object is agnostic about what its tracked by.
For example, in a music player, instead of writing code to update the
window-title in the function that starts a song, there would be a
concept of a "current song", and the window would listen for changes to
the current song, and update the title when it changes.

In ``flexx.event``, a ``HasEvents`` object keeps track of its observers
(handlers) and notifies them when there are changes. In our music player
example, there would probably be a property or readonly "current_song",
and a handler to take action when it changes.

As is common in the observer pattern, the handlers keep track of the
handlers that they observe. Therefore both handlers and ``HasEvents``
objects have a ``dispose()`` method.

Signals and slots
=================

The Qt GUI toolkit makes use of a mechanism called "signals and slots" as
an easy way to connect different components of an application. In
``flexx.event`` signals translate to readonly properties, and slots to
the handlers that connect to them.

Overloadable event handlers
===========================

In Qt, the "event system" consists of methods that handle an event, which
can be overloaded in subclasses to handle an event differently. In
``flexx.event``, a handler can be implemented simply by naming a method
``on_xx``. Doing so allows subclasses to re-implement the handler, and also
call the original handler using ``super()``.

Publisch-subscribe pattern
==========================

In pub-sub, publishers generate messages identified by a 'topic', and
subscribers can subscribe to such topics. There can be zero or more publishers
and zero or more subscribers to any topic. 

In ``flexx.event`` a `HasEvents` object can play the role of a broker.
Publishers can simply emit events. The event type represents the message
topic. Subscribers are represented by handlers.

"""

from ._dict import Dict
from ._handler import connect, loop
from ._emitters import prop, readonly, emitter
from ._hasevents import HasEvents

# from ._hasevents import new_type, with_metaclass
