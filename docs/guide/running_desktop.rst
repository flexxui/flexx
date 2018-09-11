-------------------------------------
Running Flexx on the desktop (or web)
-------------------------------------

Serving and launching apps
--------------------------

Each application has a root app component. This can be either a ``Pycomponent``
or a ``JsComponent``. The app can be wrapped into an application like so
(any additional arguments are passed to the component when it is instantiated):

.. code-block:: py

    a = app.App(PersonDatabase)

For a web server approach use ``serve()``:

.. code-block:: py

    a.serve()


The serve method registers the application, so that clients can connect
to the app based on its name (or using a custom name specified). One instance of this class is created
per connection. Multiple apps can be hosted from the same process simply
be specifying more app classes. To connect to the application
corresponding to the ``MyApp`` class, one should connect to
"http://domain:port/MyApp".

An app can also be launched:

.. code-block:: py

    a.launch()  # argument can be e.g. "app" or "firefox-browser"

This will serve the app and then invoke
a client webruntime which is connected to the app object. This
is the intended way to launch desktop-like apps.

An app can also be exported to HTML via ``a.export()``. One can
create a drectory structure that contains multiple exported apps that
share assets, or export apps as standalone html documents.

Starting the server
-------------------

Use ``app.start()`` to enter the mainloop for the server. For desktop
applications you can use ``app.run()``, which does what ``start()`` does,
except the main loop exits when there are no more connections (i.e. the
server stops when the (last) window is closed).

Flexx in the notebook
---------------------

Further, Flexx can be used interactively from the Jupyter notebook.
Use ``init_notebook()`` which will inject the necessary JS and CSS.
Also use ``%gui asyncio`` to enable the Flexx event system.
Simple widgets (e.g. buttons) will display just fine, but for other
widgets you might want to use ``SomeWidget(style='height:300px')`` to
specify its size.


Some background info on the server process
------------------------------------------

Each server process hosts on a single URL (domain+port), but can serve
multiple applications (via different paths). Each process uses one
tornado IOLoop, and exactly one Tornado Application object. Flexx' event loop
is based on asyncio (Tornado is set up to integrate with asyncio).

When a client connects to the server, it is served an HTML page, which
contains the information needed to connect to a websocket. From there,
all communication happens over this websocket, including the definition
of CSS and JavaScript modules.

