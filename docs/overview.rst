Flexx overview
--------------

.. image:: _static/overview.svg

The image above outlines the structure of Flexx. 
The *event* module provides a powerful property and event system that
makes it easy to connect different parts of your application. Central to
the event system is the ``Component`` class.
The *app* module runs the server to which the web runtime connects (via a
websocket). Further, it extends the ``Component`` class into the
``PyComponent`` and ``JsComponent`` classes. Objects of these classes 
live in Python and JavaScript respectively, but (can) have a representation
on the other side, from which properties can be accessed, and actions be invoked.
The *ui* module defines all widgets (based on ``JsComponent``).

The external *webruntime* package is used to launch a browser looking like
a dektop app. The *pscript* library is used throughout Flexx to compile
Python code to JavaScript.
