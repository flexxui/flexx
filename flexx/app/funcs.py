"""
Functional API for flexx.app
"""

import os
import sys
import json

from .. import webruntime
from .. import config

from . import model, logger
from .model import Model
from .session import manager
from .tornadoserver import server

# Make event system use of Tornado
from ..event import _loop
_loop.loop.integrate_tornado()


reprs = json.dumps

## Main loop functions


def init(**kwargs):
    """ Initialize (bind) the server and return the server object.
    
    As a user, you typically do not need this function, as it is
    automatically called by start() and run(). If called without
    arguments, this function can safely be called multiple times.
    
    The returned server object is a small wrapper around a native server
    object (available through ``server_object.native``). For now this
    is always a Tornado Application, but in the future other types of
    servers (e.g. Flask) may be supported.
    
    Arguments:
        args: currently unused. Arguments may be added at a later time (e.g.
            to chose between different server backends).
        host (str): The hostname to serve on. By default
            ``flexx.config.hostname`` is used.
        port (int, str): The port number. If a string is given, it is
            hashed to an ephemeral port number. By default
            ``flexx.config.hostname`` is used.
    """
    def _getargs(host=None, port=None):
        return host, port
    host, port = _getargs(**kwargs)
    # If already hosting, return or error
    if getattr(server, '_is_hosting', False):
        if host is None and port is None:
            return
        else:
            raise RuntimeError('Already hosting')
    # Handle defaults
    if host is None:
        host = config.hostname
    if port is None:
        port = config.port
    # Start hosting
    server.open(host, port)
    server._is_hosting = True
    return server


def start(host=None, port=None):
    """ Start the server and event loop if not already running.
    
    This function generally does not return until the application is
    stopped, although it will try to behave nicely in interactive
    environments (e.g. Spyder, IEP, Jupyter notebook), so the caller
    should take into account that the function may return immediately.
    
    If not given, the host and port specified by the config are used, e.g.
    from environment variables FLEXX_HOSTNAME and FLEXX_PORT.
    
    Arguments:
        host (str): The hostname to serve on. By default
            ``flexx.config.hostname`` is used.
        port (int, str): The port number. If a string is given, it is
            hashed to an ephemeral port number. By default
            ``flexx.config.hostname`` is used.
    """
    # Get server up
    init(host=host, port=port)
    # Start event loop
    logger.info('Starting Flexx event loop.')
    server.start()


def run():
    """ Start the event loop if not already running, for desktop apps.
    
    In contrast to ``start()``, when the server is started this way,
    it will close down when there are no more connections.
    """
    server._auto_stop = True
    return start()


def stop():
    """ Stop the event loop
    """
    server.stop()


def call_later(delay, callback, *args, **kwargs):
    """ Call the given callback after delay seconds. If delay is zero, 
    call in the next event loop iteration.
    """
    server.call_later(delay, callback, *args, **kwargs)

model.call_later = call_later  # Work around circular dependency


server._auto_stop = False
@manager.connect('connections_changed')
def _auto_closer(*events):
    if not server._auto_stop:
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
    _server_open()
    host, port = server.serving_at
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
            raise RuntimeError('already in capture mode')
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
    
    # Get session or create new, check if we already initialized notebook
    session = manager.get_default_session()
    if session is None:
        session = manager.create_default_session()
    if hasattr(session, '_init_notebook_done'):
        display(HTML("<i>Flexx already loaded</i>"))
        return  # Don't inject twice
    else:
        session._init_notebook_done = True
    
    # Install helper to make things work in exported notebooks
    NoteBookHelper(session)
    
    # Load assets
    try:
        session.use_global_asset('phosphor-all.js')
        session.use_global_asset('flexx-ui.css')
        session.use_global_asset('flexx-ui.js')
    except IndexError as err:
        pass  # Ok if it fails; assets can be loaded dynamically.
    
    # Open server - the notebook helper takes care of the JS resulting
    # from running a cell, but any interaction goes over the websocket.
    init()
    host, port = server.serving_at
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
    init()
    host, port = server.serving_at
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
