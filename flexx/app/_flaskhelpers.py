"""
This file contains the main functions used to implement a flask/gevent server
hosting a flexx application.

The chain of initialisation is the following:

# Import
from flexx import flx_flask
# Define one or multiple classes
class Example1(flx.Widget):
    ...
# Register the class to the server (you can define more than one)
flx_flask.serve(Example1)

# Instantiate the Socket class and then register all flexx apps.
# The flexx apps are individually registered as one Blueprint each.
sockets = Sockets(app)  # keep at the end
flx_flask.register_blueprints(app, sockets, static_folder='static')

# Start the flexx thread to manage the flexx asyncio worker loop.
flx_flask.start_thread()

# You can then start the flask/gevent server.

See the howtos/flask_server.py example for a working example.
"""
import flask
from ._app import manager, App
from ._server import current_server

flexxBlueprint = flask.Blueprint('FlexxApps', __name__, static_folder='static')
flexxWS = flask.Blueprint('flexxWS', __name__)

# todo remove this and implement blueprint registration/deregistration?
_blueprints_registered = False

import os
import inspect


def register_blueprints(app, sockets, **kwargs):
    """
    Register all flexx apps to flask. Flask will create one URL per application plus a
    generic /flexx/ URL for serving assets and data.

    see flexxamples/howtos/flask_server.py for a full example.
    """
    global _blueprints_registered
    if _blueprints_registered:
        return
    # Find the callers path
    frame = inspect.stack()[1]
    p = frame[0].f_code.co_filename
    caller_path = os.path.dirname(p)
    # Convert the paths in arguments to absolute paths
    for key, value in kwargs.items():
        if key in ["static_folder", 'static_url_path', 'template_folder']:
            kwargs[key] = os.path.abspath(os.path.join(caller_path, value))
    ########### Register apps ###########
    for name in manager._appinfo.keys():
        # Create blueprint - this is specific to apps
        appBlueprint = flask.Blueprint(f'Flexx_{name}', __name__, **kwargs)
        from ._flaskserver import AppHandler  # delayed import

        # Create handlers
        def app_handler():
            # AppHandler
            return AppHandler(flask.request).run()

        appBlueprint.route('/')(app_handler)
        app_handler.__name__ = name

        def app_static_handler(path):
            return appBlueprint.send_static_file(path)

        appBlueprint.route('/<path:path>')(app_static_handler)
        # register the app blueprint
        app.register_blueprint(appBlueprint, url_prefix=f"/{name}")
    # This is for the shared flexx assets
    app.register_blueprint(flexxBlueprint, url_prefix=r"/flexx")
    ########### Register sockets ###########
    sockets.register_blueprint(flexxWS, url_prefix=r"/flexx")
    _blueprints_registered = True
    return


def serve(cls):
    """
    This function registers the flexx Widget to the manager so the server can
    serve them properly from the server.
    """
    m = App(cls)
    if not m._is_served:
        m.serve()


def _start(loop):
    """
    Start the flexx event loop only. This function generally does not
    return until the application is stopped.

    In more detail, this calls ``run_forever()`` on the asyncio event loop
    associated with the current server.
    """
    server = current_server(backend='flask', loop=loop)
    server.start_serverless()


def start_thread():
    """
    Starts the flexx thread that manages the flexx asyncio worker loop.
    """
    import threading
    import asyncio

    # assign the loop to the manager so it can be accessed later.
    flexx_loop = asyncio.new_event_loop()

    def flexx_thread(loop):
        """
        Function to start a thread containing the main loop of flexx.
        This is needed as flexx is an asyncio application which is not
        compatible with flask/gevent.
        """
        asyncio.set_event_loop(loop)
        _start(loop)  # starts flexx loop without http server

    thread1 = threading.Thread(target=flexx_thread, args=(flexx_loop,))
    thread1.daemon = True
    thread1.start()
