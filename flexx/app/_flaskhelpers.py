import flask
from ._app import manager, App
from ._server import create_server, current_server

flexxBlueprint = flask.Blueprint('FlexxApps', __name__, static_folder='static')
flexxWS = flask.Blueprint('flexxWS', __name__)

_blueprints_registered = False # todo remove this and implement blueprint registration/deregistration?

def register_blueprints(app, sockets):
    """
    Register all flexx apps to flask. Flask will create one URL per application plus a
    generic /flexx/ URL for serving assets and data.
    
    see flexxamples/howtos/flask_server.py for a full example.
    """
    global _blueprints_registered
    if _blueprints_registered:
        return
    ########### Register apps ###########
    for name in manager._appinfo.keys():
        # Create blueprint
        appBlueprint = flask.Blueprint(f'Flexx_{name}', __name__, static_folder='static') # This is specific to apps
        from ._flaskserver import AppHandler # delayed import
        # Create handler
        def app_handler(path):
            # AppHandler
            return AppHandler(flask.request).run()
        app_handler.__name__ = name
        appBlueprint.route('/', defaults={'path': ''})(
            appBlueprint.route('/<path:path>')(app_handler))
        # register the app blueprint
        app.register_blueprint(appBlueprint, url_prefix=f"/{name}")
    app.register_blueprint(flexxBlueprint, url_prefix=r"/flexx") # This is for the shared flexx assets
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

def start():
    """
    Start the flexx event loop only. This function generally does not
    return until the application is stopped.

    In more detail, this calls ``run_forever()`` on the asyncio event loop
    associated with the current server.
    """
    server = current_server(backend='flask')
    server.start_serverless()