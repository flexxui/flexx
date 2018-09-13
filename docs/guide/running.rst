-----------------------
Ways to run a Flexx app
-----------------------


Run as a desktop app
--------------------

During development, and when creating a web app, you will want to use
``launch()``:

.. code-block:: py
    
    app = flx.App(MainComponent)
    app.launch('app')  # to run as a desktop app
    # app.launch('browser')  # to open in the browser
    flx.run()  # mainloop will exit when the app is closed



Flexx in Jupyter
----------------

Flexx can be used interactively from the Jupyter notebook.
Use ``flx.init_notebook()`` which will inject the necessary JS and CSS.
Also use ``%gui asyncio`` to enable the Flexx event system.
Simple widgets (e.g. buttons) will display just fine, but for other
widgets you might want to use ``SomeWidget(minsize=300)`` to
specify a minimum size.

As of yet, Flexx does not work in JupyterLab.


Serve as a web app
------------------

It is possible to serve Flexx apps and allow multiple people to connect.
Flexx provides ways to have all connected clients interact with each-other,
see e.g. the chatroom and colab-painting examples.

.. code-block:: py
    
    app = flx.App(MainComponent)
    app.serve('foo')  # Serve at http://domain.com/foo
    app.serve('')  # Serve at http://domain.com/
    flx.start()  # Keep serving "forever"

Some details:

Each server process hosts on a single URL (domain+port), but can serve
multiple applications (via different paths). Each process uses one
tornado IOLoop, and exactly one Tornado Application object. Flexx' event loop
is based on asyncio (Tornado is set up to integrate with asyncio).

When a client connects to the server, it is served an HTML page, which
contains the information needed to connect to a websocket. From there,
all communication happens over this websocket, including the definition
of CSS and JavaScript modules.

The overhead for each connection is larger than that of classic http
frameworks, and the complexity of the Python-JS interaction are a
potential risk for security issues and memory leaks. For the Flexx
`demo page <https://demo.flexx.app>`_ we run the server in an auto-restarting
Docker container with applied memory limits.


Export to a static web page
---------------------------

Any app can be exported to its raw assets. However, apps that rely on
a PyComponent won't work correctly, obviously. Exporting to a single
file won't work for apps that use session/shared data.

.. code-block:: py
    
    app = flx.App(MainComponent)
    app.export('~/myapp/index.html')  # creates a few files
    app.export('~/myapp.html', link=0)  # creates a single file


Serve as a proper web app 
-------------------------

When creating an app that will run on a long-running server and/or will be
accessed by many clients, you may want to implement the server using an
http framework such as aiohttp, flask, etc. 

You can first dump the assets to a dictionary, which you can then serve
using your library of choice. See the ``serve_with_`` examples for
complete implementations.

It's worth noting that if ``App.serve()``, ``flx.run()`` and
``flx.start()`` are not called, Flexx won't even import Tornado (and
we have a test to make sure that it stays that way). This makes it
feasible to generate the client-side of a website with Flexx when the
server starts up.

.. code-block:: py
    
    app = flx.App(MainComponent)
    assets = app.dump('index.html')
    
    ...  # serve assets with flask/aiohttp/tornado/vibora/django/... 


Next
----

Next up: :doc:`Debugging <debugging>`.
