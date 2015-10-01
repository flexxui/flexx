"""
The app module implements the connection between Python and JavaScript.

It implements a simple server based on Tornado. HTML is served to
provide the client with the JavaScript and CSS, but once connected, all
communication goed via a websocket.

A central component is the ``Pair`` class, which allows definition of
objects that have both a Python and JavaScript representation, forming
a basis for model-view-like systems.

Some background info on the server process
------------------------------------------

Each server process hosts on a single URL (domain+port), but can serve
multiple applications (via different paths). Each process uses one
tornado IOLoop (the default one), and exactly one Tornado Application
object.

Applications
------------

A ``Pair`` class can be made into an application by decorating it with
``app.serve``. This registers the application, so that clients can connect
to the app based on its name. One instance of this class is instantiated
per connection. Multiple apps can be hosted from the same process simply
be specifying more app classes. To connect to the application
corresponding to the `MyApp` class, one should connect to
"http://domain:port/MyApp".

An app can also be launched (via ``app.launch()``), which will invoke
a client webruntime which is connected to the returned app object. This
is the intended way to launch desktop-like apps. An app can also be
exported to HTML via ``app.export()``.

Further, there is a notion of a default app, intended for interactive use
and use inside the Jupyter notebook; any ``Pair`` instance created
without a ``proxy`` argument will connect to this default app.

Starting the server
-------------------

Use ``start()`` to enter the mainloop for the server. Optionally, the
hostname and port can be specified. Avoid ``sys.exit(app.start())``,
because ``start()`` may return immediately in interactive environments.

For desktop applications you can use ``run()``, which does what
``start()`` does, except the main loop exits when there are no more
connections (i.e. the server stops when the window is closed).

In the notebook
---------------

In the IPython/Jupyter notebook, the user needs to run
``init_notebook()`` which will inject JS and CSS into the browser.

For each widget that gets used as a cell output, a container DOM
element is created, in which the widget is displayed.
"""

from .proxy import run, start, stop, init_notebook, call_later
from .proxy import serve, launch, export, manager
from .pair import Pair, get_instance_by_id, get_pair_classes, no_sync
