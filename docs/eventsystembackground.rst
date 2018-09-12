-----------------------------------------
Some background on the Flexx event system
-----------------------------------------

Flexx' event system is quite flexible and designed to cover the needs
of a variety of event/messaging mechanisms. But we did not get there
in one go.


History
-------

In the early days of Flexx, the event system was based on the ideas of
reactive programming, where information supposedly flows through your
application. Although this style does have benefits, we found it very
unnatural for GUI applications. Therefore we made a major refactoring
to build an event system using a more classic property based approach.
We build in a bit of asynchronicity to deal with some of the common
problems with MVC, and were quite happy. However, as we started building
larger applications, the system started showing its limitations. Several
months of discussion and design, followed by another several months of
coding, resulted in the current event system. 



Patterns
--------

This section discusses how the event system relates to some common patterns,
and how these can be implemented.

Observer pattern
================

The idea of the observer pattern is that observers keep track (the state
of) of an object, and that an object is agnostic about what it's tracked by.
For example, in a music player, instead of writing code to update the
window-title inside the function that starts a song, there would be a
concept of a "current song", and the window would listen for changes to
the current song to update the title when it changes.

In ``flexx.event``, a ``Component`` object keeps track of its observers
(reactions) and notifies them when there are changes. In our music player
example, there would be a property "current_song", and a reaction to
take action when it changes.

As is common in the observer pattern, the reactions keep track of the
objects that they observe. Therefore both ``Reaction`` and ``Component``
objects have a ``dispose()`` method for cleaning up.

Signals and slots
=================

The Qt GUI toolkit makes use of a mechanism called "signals and slots" as
an easy way to connect different components of an application. In
``flexx.event`` signals translate to properties and assoctated setter actions,
and slots to the reactions that connect to them.

Although signals and slots provide a convenient mechanism, they make it easy
to create "spaghetti apps" where the information flows all over the place,
which is exactly what frameworks like Flux, Veux and Flexx try to overcome.

Overloadable event handlers
===========================

In Qt, the "event system" consists of methods that handles an event, which
can be overloaded in subclasses to handle an event differently. In
``flexx.event``, actions and reactions can similarly be re-implemented in
subclasses, and these can call the original handler using ``super()`` if needed.

Publish-subscribe pattern
==========================

In pub-sub, publishers generate messages identified by a 'topic', and
subscribers can subscribe to such topics. There can be zero or more publishers
and zero or more subscribers to any topic.

In ``flexx.event`` a `Component` object can play the role of a broker.
Publishers can simply emit events. The event type represents the message
topic. Subscribers are represented by handlers.
