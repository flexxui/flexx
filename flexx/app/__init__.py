"""
The app module implements the connection between Python and JavaScript.
It runs a web server and websocket server based on Tornado, provides
an asset (and data) management system, and provides the ``Model`` class,
which allows definition of objects that have both a Python and JavaScript
representation, forming the basis for widgets etc.

Some background info on the server process
------------------------------------------

Each server process hosts on a single URL (domain+port), but can serve
multiple applications (via different paths). Each process uses one
tornado IOLoop, and exactly one Tornado Application object.

When a client connects to the server, it is served an HTML page, which
contains the information needed to connect to a websocket. From there,
all communication happens over this websocket.

Applications
------------

A ``Model`` class can be made into an application by decorating it with
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
can be loaded in the client by adding it as an asset. This can be done using:

.. code-block:: py
    
    # Normal asset
    your_model.session.add_asset('mydep.js', js_code)
    
    # Sometimes a more lightweight *remote* asset is prefered
    your_model.session.add_asset('http://some.cdn/lib.css')


Data management
---------------

Data can be provided to the client in a similar way:

.. code-block:: py
    
    # Add shared data
    link = app.assets.add_shared_data('some_name.png', binary_blob)

    # Add session-specific data
    link = your_model.session.add_data('some_name.png', binary_blob)

Note that ``binary_blob`` can also be a string starting with ``http://`` or
``file://``. In the future we plan to make it easier to load arbitrary
data in the client (mainly for scientific purposes).


"""

_DEV_NOTES = """
Overview of classes:

* Model: the base class for creating Python-JS objects.
* AssetStore: one instance of this class is used to provide all client
  assets in this process (JS, CSS, images, etc.).
* SessionAssets: base class for Session that implements the assets part.
  Assets specific to the session are name-mangled.
* Session: object that handles connection between Python and JS. Has a
  websocket, and optionally a reference to the runtime.
* WebSocket: tornado WS handler.
* AppManager: keeps track of what apps are registered. Has functionality
  to instantiate apps and connect the websocket to them.
* Server: handles http requests. Uses manager to create new app
  instances or get the page for a pending session. Hosts assets by using
  the global asset store.
* FlexxJS (in clientcore.py): more or less the JS side of a session.

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
from .assetstore import assets, Asset


# def _install_assets():
#     from .clientcore import FlexxJS
#     
#     classes = assets.get_module_classes('flexx.app')
#     
#     assets.add_shared_asset(
#             name='flexx-app.js',
#             sources=[FlexxJS, 'var flexx = new FlexxJS();'] + classes,
#             deps=['pyscript-std.js'],
#             exports=['flexx'])
# 
# _install_assets()
