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
from .assetstore import assets
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
            ``flexx.config.hostname`` is used. If ``False``, do not listen
            (e.g. when integrating with an existing Tornado application).
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
    # Schedule pending calls
    _current_server.call_later(0, _loop.loop.iter)
    while _pending_call_laters:
        delay, callback, args, kwargs = _pending_call_laters.pop(0)
        call_later(delay, callback, *args, **kwargs)
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
    if not _current_server:
        _pending_call_laters.append((delay, callback, args, kwargs))
        return
    server = current_server()
    server.call_later(delay, callback, *args, **kwargs)


# Work around circular dependency
model.call_later = call_later

_pending_call_laters = []

# Integrate the "event-loop" of flexx.event
_loop.loop.integrate(lambda f: call_later(0, f))


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


def init_interactive(cls=None, runtime=None):
    """ Initialize Flexx for interactive mode. This creates a default session
    and launches a runtime to connect to it. 
    
    Parameters:
        cls (None, Model): a subclass of ``app.Model`` (or ``ui.Widget``) to use
            as the *default active model*. Only has effect the first time that
            this function is called.
        runtime (str): the runtime to launch the application in. Default 'xul'.
    """
    
    # Determine default model class (which is a Widget if ui is imported)
    if cls is None and 'flexx.ui' in sys.modules:
        from .. import ui
        cls = ui.Widget
    
    # Create the default session
    session = manager.get_default_session()
    if session is None:
        session = manager.create_default_session(cls)
    else:
        return  # default session already running

    # Launch web runtime, the server will wait for the connection
    server = current_server()
    host, port = server.serving
    url = '%s:%i/%s/?session_id=%s' % (host, port, session.app_name, session.id)
    session._runtime = launch('http://' + url, runtime=runtime)
    

class App:
    """ Specification of a Flexx class.
    
    In the strict sense, this is a container for a Model class plus the
    args and kwargs that it is to be instantiated with.
    
    Arguments:
        cls (Model): the Model class (or Widget) that represents this app.
        args: positional arguments used to instantiate the class (and received
            in its ``init()`` method).
        kwargs: keyword arguments used to initialize the model's properties.
    """
    
    def __init__(self, cls, *args, **kwargs):
        if not isinstance(cls, type) and issubclass(type, Model):
            raise ValueError('App needs a Model class as its first argument.')
        self._cls = cls
        self.args = args
        self.kwargs = kwargs
        self._path = None
    
    def __call__(self, *args, **kwargs):
        a = list(self.args) + list(args)
        kw = {}
        kw.update(self.kwargs)
        kw.update(kwargs)
        return self.cls(*a, **kw)
    
    def __repr__(self):
        t = '<App based on class %s pre-initialized with %i args and %i kwargs>'
        return t % (self.cls.__name__, len(self.args), len(self.kwargs))
    
    @property
    def cls(self):
        """ The Model class that is the basis of this app.
        """
        return self._cls
    
    @property
    def path(self):
        """ The url path that this app is served at. Is None if the app
        is not served yet.
        """
        return self._path
    
    # todo: move implementation here and make app.serve() et al. call these.
    
    def serve(self, *args, **kwargs):
        serve(self, *args, **kwargs)
    
    def launch(self, *args, **kwargs):
        launch(self, *args, **kwargs)
    
    def export(self, *args, **kwargs):
        export(self, *args, **kwargs)
    

class NoteBookHelper:
    """ Object that captures commands send to the websocket during the
    execution of a cell, and then applies these commands using a script
    node. This way, Flexx widgets keep working in the exported notebook.
    """
    
    close_code = None
    
    def __init__(self, session):
        self._session = session
        self._real_ws = None
        self._commands = []
        self.enable()
    
    def enable(self):
        from IPython import get_ipython
        ip = get_ipython()
        ip.events.register('pre_execute', self.capture)
        ip.events.register('post_execute', self.release)
    
    def capture(self):
        if self._real_ws is not None:
            logger.warn('Notebookhelper already is in capture mode.')
        else:
            assert self._session._ws is not None
            self._real_ws = self._session._ws
            self._session._ws = self
    
    def release(self):
        if self._session._ws is self:
            self._session._ws = self._real_ws
        self._real_ws = None
        if self._commands:
            from IPython.display import display, Javascript
            commands = ['flexx.command(%s);' % reprs(msg) for msg in self._commands]
            self._commands = []
            display(Javascript('\n'.join(commands)))
    
    def command(self, msg):
        self._commands.append(msg)
    
    @property
    def ping_counter(self):
        if self._session._ws is self:
            return self._real_ws.ping_counter
        else:
            return self._session._ws.ping_counter


def init_notebook():
    """ Initialize the Jupyter notebook by injecting the necessary CSS
    and JS into the browser. Note that any Flexx-based libraries that
    you plan to use should probably be imported *before* calling this.
    """
    
    # Note: not using IPython Comm objects yet, since they seem rather
    # undocumented and I could not get them to work when I tried for a bit.
    # This means though, that flexx in the notebook only works on localhost.
    
    from IPython.display import display, clear_output, HTML
    # from .. import ui  # noqa - make ui assets available
    
    # Make default log level warning instead of "info" to avoid spamming
    # This preserves the log level set by the user
    config.load_from_string('log_level = warning', 'init_notebook')
    set_log_level(config.log_level)
    
    # Get session or create new
    session = manager.get_default_session()
    if session is None:
        session = manager.create_default_session()
    
    # Open server - the notebook helper takes care of the JS resulting
    # from running a cell, but any interaction goes over the websocket.
    server = current_server()
    host, port = server.serving
    
    # Trigger loading phosphor assets
    if 'flexx.ui' in sys.modules:
        from flexx import ui
        session.register_model_class(ui.Widget)
    
    # Get assets, load all known modules to prevent dynamic loading as much as possible
    js_assets, css_assets = session.get_assets_in_order(css_reset=False, load_all=True)
    
    # Pop the first JS asset that sets flexx.app_name and flexx.session_id
    # We set these in a way that it does not end up in exported notebook.
    js_assets.pop(0)
    url = 'ws://%s:%i/flexx/ws/%s' % (host, port, session.app_name)
    flexx_pre_init = """<script>window.flexx = window.flexx || {};
                                window.flexx.app_name = "%s";
                                window.flexx.session_id = "%s";
                                window.flexx.ws_url = "%s";
                                window.flexx.is_live_notebook = true;
                        </script>""" % (session.app_name, session.id, url)
    
    # Check if already loaded, if so, re-connect
    if not getattr(session, 'init_notebook_done', False):
        session.init_notebook_done = True  # also used in assetstore
    else:
        display(HTML(flexx_pre_init))
        clear_output()
        display(HTML("""<script>
                        flexx.is_exported = !flexx.is_live_notebook;
                        flexx.init();
                        </script>
                        <i>Flexx already loaded. Reconnected.</i>
                        """))
        return  # Don't inject Flexx twice
        # Note that exporting will not work anymore since out assets
        # are no longer in the outputs
    
    # Install helper to make things work in exported notebooks
    NoteBookHelper(session)
    
    # Compose HTML to inject
    t = "<i>Injecting Flexx JS and CSS</i>"
    t += '\n\n'.join([asset.to_html('{}', 0) for asset in css_assets + js_assets])
    t += """<script>
            flexx.is_notebook = true;
            flexx.is_exported = !flexx.is_live_notebook;
            /* If Phosphor is already loaded, disable our Phosphor CSS. */
            if (window.jupyter && window.jupyter.lab) {
                document.getElementById('phosphor-all.css').disabled = true;
            }
            flexx.init();
            </script>"""
    
    display(HTML(flexx_pre_init))  # Create initial Flexx info dict
    clear_output()  # Make sure the info dict is gone in exported notebooks
    display(HTML(t))
    
    # Note: the Widget._repr_html_() method is responsible for making
    # the widget show up in the notebook output area.


def serve(cls, name=None, properties=None):
    """ Serve the given Model class as a web app. Can be used as a decorator.
    
    This registers the given class with the internal app manager. The
    app can be loaded via 'http://hostname:port/classname'.
    
    Arguments:
        cls (Model): a subclass of ``app.Model`` (or ``ui.Widget``).
        name (str): the relative URL path to serve the app on. If this is
          ``''`` (the empty string), this will be the main app.
        properties (dict, optional): the initial properties for the model. The
          model is instantiated using ``Cls(**properties)``.
    
    Returns:
        cls: The given class.
    """
    # Note: this talks to the manager; it has nothing to do with the server
    assert ((isinstance(cls, type) and issubclass(cls, Model)) or
            (isinstance(cls, App) and issubclass(cls.cls, Model)))
    manager.register_app_class(cls, name, properties or {})
    return cls


def launch(cls, runtime=None, properties=None, **runtime_kwargs):
    """ Launch the given Model class as a desktop app in the given runtime.
    
    Arguments:
        cls (type, str): a subclass of ``app.Model`` (or ``ui.Widget`). If this 
            is a string, it simply calls ``webruntime.launch()``.
        runtime (str): the runtime to launch the application in. Default 'xul'.
        properties (dict, optional): the initial properties for the model. The
          model is instantiated using ``Cls(**properties)``.
        runtime_kwargs: kwargs to pass to the ``webruntime.launch`` function.
    
    Returns:
        app (Model): an instance of the given class.
    """
    if isinstance(cls, str):
        return webruntime.launch(cls, runtime, **runtime_kwargs)
    if isinstance(cls, type) and issubclass(cls, Model):
        pass
    elif isinstance(cls, App) and issubclass(cls.cls, Model):
        pass
    else:
        raise ValueError('runtime must be a string or Model subclass.')
    
    # Create session
    name = cls.__name__
    serve(cls, name, properties)
    session = manager.create_session(name)
    
    # Launch web runtime, the server will wait for the connection
    server = current_server()
    host, port = server.serving
    if runtime == 'nodejs':
        js_assets, _ = session.get_assets_in_order()
        all_js = '\n\n'.join([asset.to_string() for asset in js_assets])
        url = '%s:%i/%s/' % (host, port, session.app_name)
        session._runtime = launch('http://' + url, runtime=runtime, code=all_js)
    else:
        url = '%s:%i/%s/?session_id=%s' % (host, port, session.app_name, session.id)
        session._runtime = launch('http://' + url, runtime=runtime, **runtime_kwargs)
    
    return session.app


def export(cls, filename=None, properties=None, single=None, link=None,
           write_shared=True):
    """ Export the given Model class to an HTML document.
    
    Arguments:
        cls (Model): a subclass of ``app.Model`` (or ``ui.Widget``).
        filename (str, optional): Path to write the HTML document to.
            If not given or None, will return the html as a string.
        properties (dict, optional): the initial properties for the model. The
          model is instantiated using ``Cls(**properties)``.
        link (int): whether to link assets or embed them:
        
            * 0: all assets are embedded.
            * 1: normal assets are embedded, remote assets remain remote.
            * 2: all assets are linked (as separate files).
            * 3: (default) normal assets are linked, remote assets remain remote.
        write_shared (bool): if True (default) will also write shared assets
            when linking to assets. This can be set to False when
            exporting multiple apps to the same location. The shared assets can
            then be exported last using ``app.assets.export(dirname)``.
    
    Returns:
        html (str): The resulting html. If a filename was specified
        this returns None.
    
    Notes:
        If the given filename ends with .hta, a Windows HTML Application is
        created.
    """
    if not (isinstance(cls, type) and issubclass(cls, Model)):
        raise ValueError('runtime must be a string or Model subclass.')
    
    # Backward comp - deprecate "single" argument at some point
    if link is None:
        if single is not None:
            logger.warn('Export single arg is deprecated, use link instead.')
            if not single:
                link = 3
    link = int(link or 0)
    
    # Prepare name, based on exported file name (instead of cls.__name__)
    name = os.path.basename(filename).split('.')[0]
    name = name.replace('-', '_').replace(' ', '_')
    
    serve(cls, name, properties)
    
    # Create session with id equal to the app name. This would not be strictly
    # necessary to make exports work, but it makes sure that exporting twice
    # generates the exact same thing (no randomly generated dir names).
    session = manager.create_session(name, name)  # 2nd arg sets session._id
    
    # Make fake connection using exporter object
    exporter = ExporterWebSocketDummy()
    manager.connect_client(exporter, session.app_name, session.id)
    
    # Clean up again - NO keep in memory to ensure two sessions dont get same id
    # manager.disconnect_client(session)
    
    # Warn if this app has data and is meant to be run standalone
    if (not link) and session.get_data_names():
        logger.warn('Exporting a standalone app, but it has registered data.')
    
    # Get HTML - this may be good enough
    html = session.get_page_for_export(exporter._commands, link)
    if filename is None:
        return html
    elif filename.lower().endswith('.hta'):
        hta_tag = '<meta http-equiv="x-ua-compatible" content="ie=edge" />'
        html = html.replace('<head>', '<head>\n    ' + hta_tag, 1)
    elif not filename.lower().endswith(('.html', 'htm')):
        raise ValueError('Invalid extension for exporting to %r' %
                         os.path.basename(filename))
    
    # Save to file. If standalone, all assets will be included in the main html
    # file, if not, we need to export shared assets and session assets too.
    filename = os.path.abspath(os.path.expanduser(filename))
    if link:
        if write_shared:
            assets.export(os.path.dirname(filename))
        session._export(os.path.dirname(filename))
    with open(filename, 'wb') as f:
        f.write(html.encode())
    
    app_type = 'standalone app' if link else 'app'
    logger.info('Exported %s to %r' % (app_type, filename))


class ExporterWebSocketDummy:
    """ Object that can be used by an app inplace of the websocket to
    export apps to standalone HTML. The object tracks the commands send
    by the app, so that these can be re-played in the exported document.
    """
    close_code = None
    
    def __init__(self):
        self._commands = []
        self.ping_counter = 0
        # todo: make icon and title work
        #self.command('ICON %s.ico' % session.id)
        # self.command('TITLE %s' % session._runtime_kwargs.get('title', 
        #                                                       'Exported flexx app'))
    
    def command(self, cmd):
        self._commands.append(cmd)
