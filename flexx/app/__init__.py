"""
The app module implements the connection between Python and JavaScript.
It runs a web server and websocket server based on Tornado, provides
an asset (and data) management system, and provides the ``Model`` class,
which allows definition of objects that have both a Python and JavaScript
representation, forming the basis for widgets etc.

Writing code with the Model class
---------------------------------

An application will typically consists of a custom Model class (or Widget).
In the class, one can define Python behavior, JavaScript behavior, define
properties etc. Using the event system explained in ``flexx.event``, one
can listen for events on either side (Python or JavaScript). Check out
the examples and this simplistic code:

.. code-block:: py

    from flexx import app, event
    
    class MyModel(app.Model):
        
        def init(self):
            ...
        
        # Listen for changes of foo in Python
        @event.connect('foo')
        def on_foo(self, *events):
            ...
        
        class Both:
            
            # A property that exists on both ends (and is synced)
            @event.property
            def foo(self, v=0):
                return v
        
        class JS:
            
            # Listen for changes of foo in JS
            @event.connect('foo')
            def on_foo(self, *events):
                ...

The scope of modules
--------------------

The above demonstrates how one can write code that is executed in JavaScript.
In this code, you can make use of functions, classes, and values that are
defined in the same module (as long as they can be transpiled / serialized).

For every Python module that defines code that is used in JS, a corresponding
JS module is created. Flexx detects what variable names are used in the JS
code, but not declared in it, and tries to find the corresponding object in
the module. You can even import functions/classes from other modules.

.. code-block:: py

    from flexx import app
    
    from foo import func1
    
    def func2():
        ...
    
    info = {'x': 1, 'y': 2}
    
    class MyModel(app.Model):
    
        class JS:
        
            @event.connect('some.event')
            def handler(self, *events):
                func1(info)
                func2()

In the code above, Flexx will include the definition of ``func2`` and
``info`` in the same module that defines ``MyModel``, and include
``func1`` in the JS module ``foo``. If the JS in ``MyModel`` would not
use these functions, neither definition would be included in the JavaScript.

One can also assign ``__pyscript__ = True`` to a module to make Flexx transpile
a module as a whole.


Applications
------------

A ``Model`` class can be made into an application by passing it to
``app.serve``. This registers the application, so that clients can connect
to the app based on its name (or using a custom name specified in
``app.serve()``). One instance of this class is created
per connection. Multiple apps can be hosted from the same process simply
be specifying more app classes. To connect to the application
corresponding to the `MyApp` class, one should connect to
"http://domain:port/MyApp".

An app can also be launched (via ``app.launch()``), which will invoke
a client webruntime which is connected to the returned app object. This
is the intended way to launch desktop-like apps.

An app can also be exported to HTML via ``app.export()``. One can
create a drectory structure that contains multiple exported apps that
share assets, or export apps as standalone html documents.

Starting the server
-------------------

Use ``app.start()`` to enter the mainloop for the server. For desktop
applications you can use ``app.run()``, which does what ``start()`` does,
except the main loop exits when there are no more connections (i.e. the
server stops when the (last) window is closed).

Interactive use
---------------

Further, Flexx can be used interactively, from an IDE or from the Jupyter
notebook. Use ``app.init_interactive()`` to launch a runtime in the same
way as ``app.launch()``, except one can now interactively (re)define models
and widgets, and make them appear in the runtime/browser.

In the IPython/Jupyter notebook, the user needs to run
``init_notebook()`` which will inject the necessary JS and CSS.
Simple widgets (e.g. buttons) will display just fine, but for other
widgets you might want to use ``SomeWidget(style='height:300px')`` to
specify its size.


Asset management
----------------

When writing code that relies on a certain JS or CSS library, that library
can be loaded in the client by creating an asset object in the module
that contains the Model class that needs it. Flexx will associate the asset
with the module, and automatically load it when code from that module
is used in JS:

.. code-block:: py
    
    # Normal asset
    asset1 = app.Asset('mydep.js', js_code)
    
    # Sometimes a more lightweight *remote* asset is prefered
    asset2 = app.asset('http://some.cdn/lib.css')
    
    # Create Model (or Widget) that needs the asset at the client
    class MyMode(app.Model):
        ....

Data management
---------------

Data can be provided per session or shared between sessions:

.. code-block:: py
    
    # Add session-specific data
    link = your_model.session.add_data('some_name.png', binary_blob)
    
    # Add shared data
    link = app.assets.add_shared_data('some_name.png', binary_blob)


Note that ``binary_blob`` can also be a string starting with ``http://`` or
``file://``. In the future we plan to make it easier to load arbitrary
data in the client (mainly for scientific purposes).

Note that this API for providing the client with data may change in a
following release. If you rely on this, please make an issue so we can
work out a smooth transition if necessary.

Some background info on the server process
------------------------------------------

Each server process hosts on a single URL (domain+port), but can serve
multiple applications (via different paths). Each process uses one
tornado IOLoop, and exactly one Tornado Application object.

When a client connects to the server, it is served an HTML page, which
contains the information needed to connect to a websocket. From there,
all communication happens over this websocket.

"""

_DEV_NOTES = """
Overview of classes:

* Model: the base class for creating Python-JS objects.
* JSModule: represents a module in JS that corresponds to a Python module.
* Asset: represents an asset.
* Bundle: an Asset subclass to represent a collecton of JSModule's in one asset.
* AssetStore: one instance of this class is used to provide all client
  assets in this process (JS, CSS, images, etc.). It also keeps track
  of modules.
* SessionAssets: base class for Session that implements the assets/data part.
* Session: object that handles connection between Python and JS. Has a
  websocket, and optionally a reference to the runtime.
* WebSocket: tornado WS handler.
* AppManager: keeps track of what apps are registered. Has functionality
  to instantiate apps and connect the websocket to them.
* Server: handles http requests. Uses manager to create new app
  instances or get the page for a pending session. Hosts assets by using
  the global asset store.
* Flexx class (in clientcore.py): more or less the JS side of a session.

"""

import logging
logger = logging.getLogger(__name__)
del logging

# flake8: noqa
from .session import manager, Session
from .model import Model, get_active_model
from .model import get_instance_by_id, get_model_classes
from .funcs import create_server, current_server, run, start, stop, call_later
from .funcs import init_interactive, init_notebook, serve, launch, export
from .assetstore import assets, Asset, Bundle, JSModule
