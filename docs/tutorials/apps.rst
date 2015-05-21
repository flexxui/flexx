============
Applications
============

Zoof.ui is all about creating applications. Although it is implemented
using web technology, Zoof.ui is very much a Python GUI toolkit. You do not
need to know anything about HTML or JavaScript in order to use it.


Desktop app or web app?
-----------------------

Zoof.ui can create applications that look and feel native.
The fact that its build with web technoligy does not necesarily mean
that your user will use the browser to view your app. We realize this
through invoking a "web-runtime", which is basically a browser that 
shows a single page and looks native.

Zoof.ui can also create web apps, and host these to many users at
the same time. It can even host multiple apps from the same process.
Therefore the way to define an app may be slightly different than the
GUI toolkit you're familiar with.


Creating an app
---------------

In Zoof.ui, you create an *app class*, and one instance of this class
is used for each "connection". Typically, an app definition looks
more or less like this:


.. code-block:: python
    
    from zoof import ui
    
    class MyApp(ui.App):
        def init(self):
            # create widgets here

    ui.run()  # Enter the main loop


The process will run an HTTP server to host your app, and an instance
of ``MyApp`` is created every time that a connection is made. The
``App.init()`` method is automatically called, and is the main place
for you to add code.

If you are developing a desktop app, (or are testing things), you can
add the following line right before the call to ``ui.run()``:
    
.. code-block:: python

    app = MyApp()

This will create an instance of your app, and also fire up a web runtime
(i.e. a browser that looks like a native app) to connect to it.


How is the app hosted?
----------------------

A process running a zoof.ui app hosts a webserver, at a specific port.
The hostname and port number can be specified, otherwise the app is hosted
at localhost and port X. If the default port cannot be used, the number
is incremened until a free port is encountered.

The app is hosted at ``http://hostname:port/AppName``.


Multiple apps
-------------

You can define multiple app classes in your main script. You can even 
import app classes from another module. When you run ``ui.run()``, the
caller namespace is inspected for app classes, and all apps are hosted.

The name of an app corresponds to the class name 
(i.e. ``SomeApp.__class__.__name__``).



Interactive use
---------------

In The IPython notebook you can instantiate an app to make it appear
inline. Also, note that there is no need for ``ui.run()``
in the IPython notebook. NOT YET IMPLEMENTED

In the IEP IDE, with the Tornado event loop integrated, ``ui.run()`` is
also not necessary (it will immediately return). The server will run
though, and you can dynamically add and/or modify elements on the
``app`` instance.


Maybe, we will also add some sort of default app, so that you won't need to create
an App class in order to show a single slider. We'll have to see how that
works out...

.. Note::
    I'm still rather new to web stuff. I thought the mechanisms outlined
    above would be useful. But some ideas might not make a lot of sense.
    Therefore, any of the above may change.
