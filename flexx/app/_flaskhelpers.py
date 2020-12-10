import flask
from ._app import manager, App
from ._server import create_server, current_server

flexxBlueprint = flask.Blueprint('FlexxApps', __name__, static_folder='static')
flexxWS = flask.Blueprint('flexxWS', __name__)

_blueprints_registered = False  # todo remove this and implement blueprint registration/deregistration?

import os
import sys
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
        # Create blueprint
        appBlueprint = flask.Blueprint(f'Flexx_{name}', __name__, **kwargs)  # This is specific to apps
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
    app.register_blueprint(flexxBlueprint, url_prefix=r"/flexx")  # This is for the shared flexx assets
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


def _start():
    """
    Start the flexx event loop only. This function generally does not
    return until the application is stopped.

    In more detail, this calls ``run_forever()`` on the asyncio event loop
    associated with the current server.
    """
    server = current_server(backend='flask')
    server.start_serverless()


def start_thread():
    import threading
    import asyncio

    def flexx_thread():
        """
        Function to start a thread containing the main loop of flexx.
        This is needed as flexx is an asyncio application which is not 
        compatible with flexx/gevent.
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        _start()  # starts flexx loop without server

    thread1 = threading.Thread(target=flexx_thread)
    thread1.daemon = True
    thread1.start()
