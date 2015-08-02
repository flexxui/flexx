"""
The react module provides functionality for Reactive Programming (RP) and
Functional Reactive Programming (FRP).

Where event-driven programming is about reacting to things that happen,
RP is about staying up to date with changing signals.

Signals
-------

A signal can be created by decorating a function. In RP-speak, the
function is "lifted" to a signal:

```python
@react.act('name')
def greet(n):
    print('hello %!' % name)
```

The example above looks quite similar to how some event-drive applications
allow binding callbacks to events. There are, however, a few differences:

* The upsteam signal that we connect to is specified using a string.
  This may seem unusual at first, but it allows easy binding for signals
  on classes, allow signal loops, and has other advantages that we'll
  discuss when we talk about dynamism.
* The `greet` object has now become a signal object, which has an output
  of its own (although the output is None in this case, because the
  function does not return a value, more on that below).
* The function (which we'd call the "callback" in an event driven
  system) does not accept an event object, but a value that corresponds
  to the upstream signal.

One other major advantage of a RP system is that signals can *connect to
multiple upsteam signals*:

```python
@react.act('first_name', 'last_name')
def greet(first, last):
    print('hello %s %s!' % (first, last)
```

This is a feature that saves a lot of overhead. For any "callback" that
you define, you specify *exactly* what input signals there are, and it will
always be up to date. Doing that in an event-driven system quickly results
in a spaghetti of callbacks and boilerplate to keep track of state.

Act signals
-----------

The two examples above show how to create an *act signal*. The function
of this signal gets called directly when any of the upstream signals
(or the upstream-upstream signals) change. It is most similar to
callbacks in an event-driven system. These signals will usually not
have an output value, but they certainly can have one.

Source and input signals
------------------------

Signals must start somewhere. The *source signal* has a `_set()` method
that the programmer can use to set the value of the signal:

```python
@react.source
def name(n):
    return n
```

The function for this source signal is very simple. You usually want
to do some input checking and/or normalization here. Especialy if the input
comes from the user, as is the case with the input signal. 

The *input signal* is a source signal that can be called with an argument
to set its value:

```python
@react.input
def name(n='john doe'):
    if not isinstance(n, str):
        raise ValueError('Name must be a string')
    return n.capitalized()

# And later ...
name('jane doe')
```

You can also see how the default value of the function argument can be
used to specify the initial signal value.

Source and input signals generally do not have upstream signals, but
they can have them.

Watch signals
-------------

In contrast to act signals, a *watch signal* does not update immediately
when the upstream signals change. It is updated automatically (lazily)
whenever its value is queried, either because the signal is called, or
because there is an act signal downstream.

Watch signals are great for passing and modifying signal values, and
its what you should probably use unless you need an input or act signal:

```python
@react.watch('first_name', 'last_name')
def full_name(first, 'last'):
    return '%s %s' % (first, last)
```

A complete example
------------------

```python
@react.input
def first_name(s='john'):
    return str(s)

@react.input
def last_name(s='doe'):
    return str(s)

@react.source
def capitalize(b=True):
    return bool(b))

@react.watch('first_name', 'last_name')
def full_name(first, 'last'):
    return '%s %s' % (first, last)

@react.watch('full_name', 'capitalize')
def full_name_capitalize(name, cap):
    if cap:
        name = name.capitalized()
    return name

@react.act('full_name_capitalize')
def greet(name):
    print('hello %s!' % name)
```

This example uses a lot of signals to just show a greeting, but it shows
some interesting points. Imagine that combining the names would be an
expensive process, and capitalizing a cheap post-processing step. The
updating of ``full_name`` would only be done when either the first or
last name changes. When the capitalize flag changes, the cached value
of `full_name` is re-used.

"""

from .react import source, input, watch, act, HasSignals, SignalValueError
from .react import Signal, SourceSignal, InputSignal, WatchSignal, ActSignal


class TestDocs(HasSignals):
    
    @input
    def title(v=''):
        """ The title of the x. """
        return str(v)
    
    @watch('xx')
    def foo(v=''):
        return v
        
    @act('title')
    def show_title(self, v):
        """ Reactor to show the title when it changes. """
        print(v)
