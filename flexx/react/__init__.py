"""
The react module provides functionality for Reactive Programming (RP) and
Functional Reactive Programming (FRP).

It is a bit difficult to explain what FRP really is. This is because
every implementation has its own take on it, and because it requires a
bit of a paradigm shift compared to classic event-driven programming.

FRP does not have to be difficult and we think our implementation of
``flexx.react`` is relatively easy to use. This brief guide takes you
through some of the FRP aspects using code examples.

What is FRP
-----------

(Don't worry if the next two paragraphs sound confusing;
things should start to make sense when we explain thing using code.)

*Where event-driven programming is about reacting to things that happen,
RP is about staying up to date with changing signal values.*

In RP the different components in an application communicate via streams
of data. In other words, components keep track of (and react to) the
*signal values* of other components. All signals (except source/input
signals) have one or more upstream signals, and can combine and or
modify these to produce a new signal value. The value of each signal
is *cached*, so that the operations applied to the signal values only
have to be performed when any upstream signal has changed. When a signal
changes its value, it will *notify* its downstream signals, so that
everything stays up-to-date.

In ``flexx.react`` signals are addressed using a string. This may seem
unusual at first, but it allows easy binding for signals on classes,
allow signal loops, and has other advantages such as dynamism.


Signals
-------

A signal can be created by decorating a function. In RP-speak, the
function is "lifted" to a signal:

.. code-block:: py
    
    # The function greet() is used to react to signal "name"
    @react.connect('name')
    def greet(n):
        print('hello %s!' % n)


The example above looks quite similar to how some event-drive applications
allow binding callbacks to events. There are, however, a few differences:
a) The greet function has now become a signal object, which has an output
of its own (although the output is None in this case, because the
function does not return a value, more on that below); b) The function
(which we'd call the "callback" in an event driven system) does not
accept an event object, but a value that corresponds to the upstream
signal value.

One other advantage of a RP system is that signals can *connect to
multiple upsteam signals*:

.. code-block:: py

    @react.connect('first_name', 'last_name')
    def greet(first, last):
        print('hello %s %s!' % (first, last)

This is a feature that saves a lot of overhead. For any "callback" that
you define, you specify *exactly* what input signals there are, and it will
always be up to date. Doing that in an event-driven system quickly results
in a spaghetti of callbacks and boilerplate to keep track of state.

The function of a signal gets called directly when any of the
upstream signals (or the upstream-upstream signals) change. The return value
of the function represents the output signal value, which can also be None.
When the return value is ``undefined`` (from ``react.undefined`` or
``pyscript.undefined``), the value is ignored and the signal maintains
its current value.


Source and input signals
------------------------

Signals must start somewhere. The *source signal* has a ``_set()`` method
that the programmer can use to set the value of the signal:

.. code-block:: py

    @react.source
    def name(n):
        return n

The function for this source signal is very simple. You usually want
to do some input checking and/or normalization here. Especialy if the input
comes from the user, as is the case with the input signal. 

The *input signal* is a source signal that can be called with an argument
to set its value:

.. code-block:: py

    @react.input
    def name(n='john doe'):
        if not isinstance(n, str):
            raise ValueError('Name must be a string')
        return n.capitalized()
    
    # And later ...
    name('jane doe')

You can also see how the default value of the function argument can be
used to specify the initial signal value.

Source and input signals generally do not have upstream signals, but
they can have them.


A complete example
------------------

.. code-block:: py
    
    @react.input
    def first_name(s='john'):
        return str(s)
    
    @react.input
    def last_name(s='doe'):
        return str(s)
    
    @react.connect('first_name', 'last_name')
    def full_name(first, 'last'):
        return '%s %s' % (first, last)
    
    @react.connect('full_name')
    def greet(name):
        print('hello %s!' % name)


Lazy signals
------------

In contrast to normal signals, a *lazy signal* does not update immediately
when the upstream signals changes. It is updated automatically (lazily)
whenever its value is queried. Note that this has little effect when
there is a normal signal downstream.

Lazy signals can be convenient in a situation where values changes rapidly,
while the current value is only needed sparingly. To create, use the
``lazy()`` decorator:

.. code-block:: py

    @react.lazy('first_name', 'last_name')
    def full_name(first, last):
        return '%s %s' % (first, last)


Caching
-------

.. code-block:: py
    
    @react.input
    def data_select(id):
        return str(id)
    
    @react.input
    def data_clean(clean):
        return bool(clean)
    
    @react.connect('data_select')
    def data(id):
        open_connection(id)
        return get_data_from_the_web()  # this may take a while
    
    @react.connect('data', 'data_clean')
    def show_data(data, clean):
        if clean:
           data = clean_func(data)
        plotter.show(data)

This hypothetical example shows how caching helps keep apps efficient.
The ``data`` signal will only update when the ``data_select`` changes.
When ``data_clean`` is changes, the ``show_data`` signal updates, but
it will use the cached value of the data.


The HasSignals class
--------------------

It is often convenient to create classes that have signals. To do so,
inherit from the ``HasSignals`` class:

.. code-block:: py

    class Person(react.HasSignals):
        def __init__(self, father):
            assert isinstance(father, Person)
            self.father = father
            react.HasSignals.__init__(self)
            
        @react.input
        def first_name(s):
            return s
        
        @react.connect('father.last_name')
        def last_name(s):
            return s
        
        @react.connect('first_name', 'last_name')
        de greet(first, last):
            print('hello %s %s!' % (first, last))

The above example show how you can directly refer to signals on the
object using their name, and even use dot notation to address the signal
of an attribute of the object.

It also shows that the signal functions do not have a ``self`` argument.
They do not have to, but they can if they needs access to the instance.

Dynamism
--------

With dynamism, you can refer to signals of signals, and have the signal
connections be made automatically. Let's modify the last example a bit:

.. code-block:: py
    
    class Person(react.HasSignals):
        def __init__(self, father):
        self.father(father)
        react.HasSignals.__init__(self)
        
        @react.input
        def father(f):
            assert isinstance(f, Person)
            return f
        
        @react.connect('father.last_name')
        def last_name(s):
            return s
        ...

In this case, the last name of the father will change when either the father
changes, or the father changes its name. Dynamism also supports star notation:


.. code-block:: py
    
    class Person(react.HasSignals):
        
        @react.input
        def children(cc):
            assert isinstance(cc, tuple)
            assert all([isinstance(c, Person) for c in cc])
            return cc
        
        @react.connect('children.*')
        def child_names(*names):
            return ', '.join(name)


Signal history
--------------

The signal object provides a bit more information than only its value.
The most notable is the value of the signal before the last change.

.. code-block:: py
    
    class Person(react.HasSignals):
        
        @react.connect('first_name'):
        def react_to_name_change(self, new_name):
            old_name = self.first_name.last_value
            new_name = self.first_name.value  # == new_name

The signal value also holds information on value update times, but this
is currently private. We'll have to see if this is reliable and
convenient enough to make it public.


Functional RP
-------------

The "F" in FRP stands for functional. Currently, there is limited
support for that, for example:

.. code-block:: py

    filter = lambda x: x>0
    @react.connect(react.filter(filter, 'number'))
    def show_positive_numbers(v):
        print(v)

This functionality is to be extended in the future.


Some things just are events
---------------------------

Many things can be described as changing signal values. Even
"left_mouse_down" works pretty well. However, some things really *are*
events, like key presses and timers. How to handle these is still
something we'd need to work out ...

"""

from .signals import SignalValueError, Signal, undefined  # noqa
from .signals import Signal, SourceSignal, InputSignal, LazySignal  # noqa
from .decorators import connect, source, input, lazy, nosync  # noqa
from .hassignals import HasSignals  # noqa
from .functional import map, filter, reduce, merge  # noqa

import logging
logging.warn('flexx.react is likely to be replaced for a different event system')
