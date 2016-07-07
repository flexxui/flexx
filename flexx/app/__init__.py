"""
The app module implements the connection between Python and JavaScript.

It implements a simple server based on Tornado. HTML is served to
provide the client with the JavaScript and CSS, but once connected, all
communication goed via a websocket.

A central component is the ``Model`` class, which allows definition of
objects that have both a Python and JavaScript representation, forming
a basis for model-view-like systems.

Some background info on the server process
------------------------------------------

Each server process hosts on a single URL (domain+port), but can serve
multiple applications (via different paths). Each process uses one
tornado IOLoop, and exactly one Tornado Application object.

Applications
------------

A ``Model`` class can be made into an application by decorating it with
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

Starting the server
-------------------

Use ``start()`` to enter the mainloop for the server. For desktop
applications you can use ``run()``, which does what ``start()`` does,
except the main loop exits when there are no more connections (i.e. the
server stops when the window is closed).

In the notebook
---------------

In the IPython/Jupyter notebook, the user needs to run
``init_notebook()`` which will inject JS and CSS into the browser.
Simple widgets (e.g. buttons) will display just fine, but for other
widgets you might want to use ``SomeWidget(style='height:300px')`` to
specify its size.

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
from .funcs import init_notebook, serve, launch, export
from .assetstore import assets
from .clientcore import FlexxJS

from ..pyscript.stdlib import get_full_std_lib as _get_full_std_lib


_JS_TEMPLATE = "%s\nvar flexx = new FlexxJS();"

assets.add_asset('pyscript-std.js', _get_full_std_lib().encode())
assets.create_module_assets('flexx.app', js=_JS_TEMPLATE % FlexxJS)
