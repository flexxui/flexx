"""
Functional API for flexx.app
"""

import os
import sys
import json

from .. import webruntime, config, set_log_level

from . import model, logger
from .model import Model
from .session import manager
from .tornadoserver import TornadoServer
from ..event import _loop

reprs = json.dumps

## Main loop functions


# There is always a single current server (except initially there is None)
_current_server = None


def create_server(host=None, port=None, new_loop=False, backend='tornado'):
    """
    Create a new server object. This is automatically called; users generally
    don't need this, unless they want to explicitly specify host/port,
    create a fresh server in testing scenarios, or run Flexx in a thread.
    
    Flexx uses a notion of a single current server object. This function
    (re)creates that object. If there already was a server object, it is
    replaced. It is an error to call this function if the current server
    is still running.
    
    Arguments:
        host (str): The hostname to serve on. By default
            ``flexx.config.hostname`` is used.
        port (int, str): The port number. If a string is given, it is
            hashed to an ephemeral port number. By default
            ``flexx.config.port`` is used.
        new_loop (bool): Whether to create a fresh Tornado IOLoop instance,
            which is made current when ``start()`` is called. If ``False``
            (default) will use the current IOLoop for this thread.
        backend (str): Stub argument; only Tornado is currently supported.
    
    Returns:
        server: The server object, see ``current_server()``.
    """
    global _current_server
    if backend.lower() != 'tornado':
        raise RuntimeError('Flexx server can only run on Tornado (for now).')
    # Handle defaults
    if host is None:
        host = config.hostname
    if port is None:
        port = config.port
    # Stop old server
    if _current_server:
        _current_server.close()
    # Start hosting
    _current_server = TornadoServer(host, port, new_loop)
    return _current_server


def current_server():
    """
    Get the current server object. Creates a server if there is none.
    Currently, this is always a TornadoServer object, which has properties:
    
    * serving: a tuple ``(hostname, port)`` specifying the location
      being served (or ``None`` if the server is closed).
    * app: the ``tornado.web.Application`` instance
    * loop: the ``tornado.ioloop.IOLoop`` instance
    * server: the ``tornado.httpserver.HttpServer`` instance
    """
    if not _current_server:
        create_server()
    return _current_server


def start():
    """
    Start the server and event loop. This function generally does not
    return until the application is stopped (although it may in
    interactive environments (e.g. Pyzo)).
    """
    server = current_server()
    logger.info('Starting Flexx event loop.')
    server.start()


def run():
    """
    Start the event loop in desktop app mode; the server will close
    down when there are no more connections.
    """
    server = current_server()
    server._auto_stop = True
    return start()


def stop():
    """
    Stop the event loop. This function is thread safe (it can be used
    even if ``flexx.start()`` was called from another thread). 
    The server can be restarted after it has been stopped. Note that
    calling ``stop()`` too often will cause a subsequent call to `start()``
    to return almost immediately.
    """
    server = current_server()
    server.stop()


def call_later(delay, callback, *args, **kwargs):
    """
    Schedule a function call in the current event loop. This function is
    thread safe.
    
    Arguments:
        delay (float): the delay in seconds. If zero, the callback will
            be executed in the next event loop iteration.
        callback (callable): the function to call.
        args: the positional arguments to call the callback with.
        kwargs: the keyword arguments to call the callback with.
    """
    server = current_server()
    server.call_later(delay, callback, *args, **kwargs)


# Work around circular dependency
model.call_later = call_later

# Integrate the "event-loop" of flexx.event
_loop.loop.integrate(lambda f: current_server().call_later(0, f))


@manager.connect('connections_changed')
def _auto_closer(*events):
    server = current_server()
    if not getattr(server, '_auto_stop', False):
        return
    for name in manager.get_app_names():
        proxies = manager.get_connections(name)
        if proxies:
            return
    else:
        logger.info('Stopping Flexx event loop.')
        server.stop()


## App functions



def _deprecated_init_interactive(runtime=None, **runtime_kwargs):
    """ Initialize Flexx for use in interactive mode.
    
    This would need a bit of code in the Widget class to automatically
    use the default app as the parent if no parent is set. But
    autosetting parents seems wrong, and explicitly setting parents (as
    in hello_world1.py) seems like not too much work, and for more ease,
    one can use a notebook. Keeping this as a reference, for now.
    """
    
    session = manager.create_default_session()
    
    # Insert container widget
    if 'flexx.ui' in sys.modules:
        from .. import ui
        session._set_app(ui.Widget(is_app=True))
    
    # Launch web runtime, the server will wait for the connection
    server = current_server()
    host, port = server.serving
    if runtime == 'nodejs':
        all_js = session.get_js_only()
        url = '%s:%i/%s/' % (host, port, session.app_name)
        session._runtime = launch('http://' + url, runtime=runtime, code=all_js)
    else:
        url = '%s:%i/%s/?session_id=%s' % (host, port, session.app_name, session.id)
        session._runtime = launch('http://' + url, runtime=runtime, **runtime_kwargs)


class NoteBookHelper:
    """ Object that captures commands send to the websocket during the
    execution of a cell, and then applies these commands using a script
    node. This way, Flexx widgets keep working in the exported notebook.
    """
    
    close_code = None
    
    def __init__(self, session):
        self._session = session
        self._ws = None
        self._commands = []
        self.enable()
    
    def enable(self):
        from IPython import get_ipython
        ip = get_ipython()
        ip.events.register('pre_execute', self.capture)
        ip.events.register('post_execute', self.release)
    
    def capture(self):
        if self._ws is not None:
            logger.warn('Notebookhelper already is in capture mode.')
        else:
            self._ws = self._session._ws
            self._session._ws = self
    
    def release(self):
        self._session._ws = self._ws
        self._ws = None
        
        from IPython.display import display, Javascript
        commands = ['flexx.command(%s);' % reprs(msg) for msg in self._commands]
        self._commands = []
        display(Javascript('\n'.join(commands)))
    
    def command(self, msg):
        self._commands.append(msg)


def init_notebook():
    """ Initialize the Jupyter notebook by injecting the necessary CSS
    and JS into the browser. Note that any Flexx-based libraries that
    you plan to use should probably be imported *before* calling this.
    """
    
    # Note: not using IPython Comm objects yet, since they seem rather
    # undocumented and I could not get them to work when I tried for a bit.
    # This means though, that flexx in the notebook only works on localhost.
    
    from IPython.display import display, HTML
    # from .. import ui  # noqa - make ui assets available
    
    # Make default log level warning instead of "info" to avoid spamming
    # This preserves the log level set by the user
    config.load_from_string('log_level = warning', 'init_notebook')
    set_log_level(config.log_level)
    
    # Get session or create new, check if we already initialized notebook
    session = manager.get_default_session()
    if session is None:
        session = manager.create_default_session()
    if getattr(session, 'init_notebook_done', False):
        display(HTML("<i>Flexx already loaded</i>"))
        return  # Don't inject twice
    else:
        session.init_notebook_done = True  # also used in assetstore
    
    # Install helper to make things work in exported notebooks
    NoteBookHelper(session)
    
    # Try loading assets for flexx.ui. This will only work if flexx.ui
    # is imported. This is not strictly necessary, since Flexx can
    # dynamically load the assets, but it seems nicer to do it here.
    try:
        session.use_global_asset('phosphor-all.js')
        session.use_global_asset('flexx-ui.css')
        session.use_global_asset('flexx-ui.js')
    except IndexError:
        pass
    
    # Open server - the notebook helper takes care of the JS resulting
    # from running a cell, but any interaction goes over the websocket.
    server = current_server()
    host, port = server.serving
    asset_elements = session.get_assets_as_html()
    
    # Compose HTML to inject
    url = 'ws://%s:%i/%s/ws' % (host, port, session.app_name)
    t = "<i>Injecting Flexx JS and CSS</i>"
    t += '\n\n'.join(asset_elements)
    t += "<script>flexx.ws_url='%s'; " % url
    t += "flexx.is_notebook=true; flexx.init();</script>"
    
    # Note: the Widget._repr_html_() method is responsible for making
    # the widget show up in the notebook output area.
    display(HTML(t))


def serve(cls):
    """ Serve the given Model class as a web app. Can be used as a decorator.
    
    This registers the given class with the internal app manager. The
    app can be loaded via 'http://hostname:port/classname'.
    
    Arguments:
        cls (Model): a subclass of ``app.Model`` (or ``ui.Widget``).
    
    Returns:
        cls: The given class.
    """
    # Note: this talks to the manager; it has nothing to do with the server
    assert isinstance(cls, type) and issubclass(cls, Model)
    manager.register_app_class(cls)
    return cls


def launch(cls, runtime=None, **runtime_kwargs):
    """ Launch the given Model class as a desktop app in the given runtime.
    
    Arguments:
        cls (type, str): a subclass of ``app.Model`` (or ``ui.Widget`). If this 
            is a string, it simply calls ``webruntime.launch()``.
        runtime (str): the runtime to launch the application in. Default 'xul'.
        runtime_kwargs: kwargs to pass to the ``webruntime.launch`` function.
    
    Returns:
        app (Model): an instance of the given class.
    """
    if isinstance(cls, str):
        return webruntime.launch(cls, runtime, **runtime_kwargs)
    if not (isinstance(cls, type) and issubclass(cls, Model)):
        raise ValueError('runtime must be a string or Model subclass.')
    
    # Create session
    serve(cls)
    session = manager.create_session(cls.__name__)
    
    # Launch web runtime, the server will wait for the connection
    server = current_server()
    host, port = server.serving
    if runtime == 'nodejs':
        all_js = session.get_js_only()
        url = '%s:%i/%s/' % (host, port, session.app_name)
        session._runtime = launch('http://' + url, runtime=runtime, code=all_js)
    else:
        url = '%s:%i/%s/?session_id=%s' % (host, port, session.app_name, session.id)
        session._runtime = launch('http://' + url, runtime=runtime, **runtime_kwargs)
    
    return session.app


def export(cls, filename=None, single=True):
    """ Export the given Model class to an HTML document.
    
    Arguments:
        cls (Model): a subclass of ``app.Model`` (or ``ui.Widget``).
        filename (str, optional): Path to write the HTML document to.
            If not given or None, will return the html as a string.
        single (bool): If True, will include all JS and CSS dependencies
            in the HTML page. If False, you want to export all assets
            using ``app.assets.export(dirname)``.
    
    Returns:
        html (str): The resulting html. If a filename was specified
        this returns None.
    """
    if not (isinstance(cls, type) and issubclass(cls, Model)):
        raise ValueError('runtime must be a string or Model subclass.')
    
    # Create session
    serve(cls)
    session = manager.create_session(cls.__name__)
    
    # Make fake connection using exporter object
    exporter = ExporterWebSocketDummy()
    manager.connect_client(exporter, session.app_name, session.id)
    
    # Clean up again - NO keep in memory to ensure two sessions dont get same id
    # manager.disconnect_client(session)
    
    # Get HTML - this may be good enough
    html = session.get_page_for_export(exporter._commands, single)
    if filename is None:
        return html
    
    # Save to file
    if filename.startswith('~'):
        filename = os.path.expanduser(filename)
    with open(filename, 'wb') as f:
        f.write(html.encode())
    logger.info('Exported app to %r' % filename)


class ExporterWebSocketDummy:
    """ Object that can be used by an app inplace of the websocket to
    export apps to standalone HTML. The object tracks the commands send
    by the app, so that these can be re-played in the exported document.
    """
    close_code = None
    
    def __init__(self):
        self._commands = []
        # todo: make icon and title work
        #self.command('ICON %s.ico' % session.id)
        # self.command('TITLE %s' % session._runtime_kwargs.get('title', 
        #                                                       'Exported flexx app'))
    
    def command(self, cmd):
        self._commands.append(cmd)
