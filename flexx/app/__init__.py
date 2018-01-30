"""
The app module implements the connection between Python and JavaScript.
It runs a web server and websocket server based on Tornado, provides
an asset (and data) management system, and provides the
:class:`PyComponent <flexx.app.PyComponent>` and
:class:`JsComponent <flexx.app.JsComponent>` classes, which form the
basis for e.g. Widgets.

Writing app components
----------------------

A Flexx application consists of components that exist in either Python or
JavaScript, and which can communicate with each-other in a variety of ways.

:class:`PyComponent <flexx.app.PyComponent>` and
:class:`JsComponent <flexx.app.JsComponent>` are
:class:`Component <flexx.event.Component>` classes that are associated with a
:class:`Session <flexx.app.Session>`, and live in Python and JavaScript,
respectively. A ``PyComponent`` always has a corresponding proxy object
in JavaScript. A ``JsComponent`` *may* have a proxy object in Python;
These proxy objects are created automatically when Python references
the component.

The proxy objects allows the "other side" to inspect properties, invoke
actions and connect to events. The component is aware of what events
the proxy has reactions for, and will only communictate these events.

A ``PyComponent`` can only be instantiated in Python, a ``JsComponent`` can
be instantiated in both Python and JavaScript.


An example:

.. code-block:: py

    from flexx import app, event
    
    class Person(app.JsComponent):
        firstname = event.StringProp(settable=True)
        lastname = event.StringProp(settable=True)
    
    class PersonDatabase(app.PyComponent):
        persons = event.ListProp()
        
        @event.action
        def add_person(self, firstname, lastname):
            p = Person(firstname=firstname, lastname=lastname)
            self._mutate_persons([p], 'insert', 99999)


In the above code, the database can be used to create new ``Person`` objects,
which live in JS. In practice, these will e.g. have a visual representation in
the browser. The database could be a ``JsComponent`` as well, but let's assume
that we need it in Python because it synchronizes to a mysql database or something.

Now what if we also want to add persons from JavaScript? We only have to get the
database object (or a proxy object, really) into a JsComponent. For example:

.. code-block:: py

    class PersonView(app.JsComponent):
        
        def init(self, db):
            self.db = db
            # now we can call self.db.add_person() from JavaScript!
    
    ...
    
    # Somewhere in Python ...
    PersonView(database)


Note that ``PyComponents`` can instantiate ``JsComponents``, but not the other
way around. Therefore, the root of an app is formed by ``PyComponents``.
It depend on the needs of an application how much ``PyComponents`` are used, if any.


The scope of modules
--------------------

Inside the methods of a component you can make use of functions, classes, and
values that are defined in the same module. Even in a ``JsComponent``
(as long as they can be transpiled / serialized).

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
    
    class MyComponent(app.JsComponent):

        @event.reaction('some.event')
        def handler(self, *events):
            func1(info)
            func2()

In the code above, Flexx will include the definition of ``func2`` and
``info`` in the same module that defines ``MyComponent``, and include
``func1`` in the JS module ``foo``. If ``MyComponent`` would not
use these functions, neither definition would be included in the JavaScript.

A useful feature is that the ``RawJS`` class from PyScript can be used
in modules to define objects in JS:

.. code-block:: py

    from flexx import app
    
    my_js_module = RawJS('require("myjsmodule.js")')
    
    class MyComponent(app.JsComponent):
    
        class JS:
        
            @event.reaction('some.event')
            def handler(self, *events):
                my_js_module.foo.bar()

One can also assign ``__pyscript__ = True`` to a module to make Flexx
transpile a module as a whole. A downside is that (at the moment) such
modules cannot use import.


Local properties
----------------

Regular methods of a ``JsComponent`` are only available in JavaScript. On the
other hand, all properties are available on the proxy object as well. This may
not always be useful. It is possible to create properties that are local
to JavaScript (or to Python in a ``PyComponent``) using ``app.LocalProp``.
An alternative may also be to use ``event.Attribute``; these are also local
to JavaScript/Python.


Serving and launching apps
--------------------------

Each application has a root app component. This can be either a ``Pycomponent``
or a ``JsComponent``. The app can be wrapped into an application like so
(any additional arguments are passed to the component when it is instantiated):

.. code-block:: py
    
    root = app.App(PersonDatabase)

For a web server approach use ``serve()``:

.. code-block:: py
    
    root.serve()
    

The serve method registers the application, so that clients can connect
to the app based on its name (or using a custom name specified). One instance of this class is created
per connection. Multiple apps can be hosted from the same process simply
be specifying more app classes. To connect to the application
corresponding to the `MyApp` class, one should connect to
"http://domain:port/MyApp".

An app can also be launched:

.. code-block:: py
    
    root.launch()  # argument can be e.g. "app" or "firefox-browser"

This will serve the app and then invoke
a client webruntime which is connected to the app object. This
is the intended way to launch desktop-like apps.

An app can also be exported to HTML via ``App.export()``. One can
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

Further, Flexx can be used interactively from the Jupyter notebook.
Use ``init_notebook()`` which will inject the necessary JS and CSS.
Also use ``%gui asyncio`` to enable the Flexx event system.
Simple widgets (e.g. buttons) will display just fine, but for other
widgets you might want to use ``SomeWidget(style='height:300px')`` to
specify its size.


Asset management
----------------

When writing code that relies on a certain JS or CSS library, that library
can be loaded in the client by associating it with the module that needs it.
Flexx will then automatically load it when code from that module is used in JS:

.. code-block:: py
    
    # Associate asset
    app.assets.associate_asset(__name__, 'mydep.js', js_code)
    
    # Sometimes a more lightweight *remote* asset is prefered
    app.assets.associate_asset(__name__, 'http://some.cdn/lib.css')
    
    # Create component (or Widget) that needs the asset at the client
    class MyComponent(app.JsComponent):
        ....

It is also possible to provide assets that are not automatically loaded
on the main app page, e.g. for sub-pages or web workers:

.. code-block:: py
    
    # Register asset
    asset_url = app.assets.add_shared_asset('mydep.js', js_code)


Data management
---------------

Data can be provided per session or shared between sessions:

.. code-block:: py
    
    # Add session-specific data
    link = my_component.session.add_data('some_name.png', binary_blob)
    
    # Add shared data
    link = app.assets.add_shared_data('some_name.png', binary_blob)

Note that it is also possible to send data from Python to JS via an
action invokation (the data is send over the websocket in this case).


Some background info on the server process
------------------------------------------

Each server process hosts on a single URL (domain+port), but can serve
multiple applications (via different paths). Each process uses one
tornado IOLoop, and exactly one Tornado Application object.

When a client connects to the server, it is served an HTML page, which
contains the information needed to connect to a websocket. From there,
all communication happens over this websocket, including the definition
of CSS and JavaScript modules.

"""

_DEV_NOTES = """
Overview of classes:

* PyComponent and JsComponent: the base class for creating Python/JS component.
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
* Flexx class (in _clientcore.py): more or less the JS side of a session.

"""

import logging
logger = logging.getLogger(__name__)
del logging

# flake8: noqa
from ._app import App, manager
from ._asset import Asset, Bundle
from ._component2 import BaseAppComponent, LocalComponent, ProxyComponent
from ._component2 import PyComponent, JsComponent, StubComponent
from ._component2 import get_component_classes, LocalProperty

from ._funcs import run, start, stop
from ._funcs import init_notebook, serve, launch, export
from ._server import create_server, current_server
from ._session import Session
from ._modules import JSModule
from ._assetstore import assets
from ._clientcore import serializer

# Resolve cyclic dependencies, and explicit exports to help cx_Freeze
from . import _tornadoserver
from . import _component2
_component2.manager = manager
