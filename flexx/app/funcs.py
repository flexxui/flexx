"""
Functional API for flexx.app
"""

import os
import time
import inspect
import logging

from ..util.icon import Icon
from .. import webruntime
from .. import react

from .pair import Pair
from .proxy import Proxy, manager
from .assetstore import assets
from .tornadoserver import server


## Main loop functions

def _server_open(host=None, port=None):
    """ Server.open() but with handling of defaults, and checking if
    already serving.
    """
    # If already hosting, return or error
    if getattr(server, '_is_hosting', False):
        if host is None and port is None:
            return
        else:
            raise RuntimeError('Already hosting')
    # Handle defaults
    if host is None:
        host = os.getenv('FLEXX_HOSTNAME', 'localhost')
    if port is None:
        port = os.getenv('FLEXX_PORT', None)
    # Start hosting
    server.open(host, port)
    server._is_hosting = True


def start(host=None, port=None):
    """ Start the server and event loop if not already running.
    
    This function generally does not return until the application is
    stopped, although it will try to behave nicely in interactive
    environments (e.g. Spyder, IEP, Jupyter notebook), so the caller
    should take into account that the function may return immediately.
    
    The host and port can also be specified using environment variables
    FLEXX_HOSTNAME and FLEXX_PORT.
    
    Arguments:
        host (str): The hostname to serve on. Default 'localhost'. This
            parameter is ignored if the server was already running.
        port (int, str): The port number. If a string is given, it is
            hashed to an ephemeral port number. If not given or None,
            will try a series of ports until one is found that is free.
    """
    # Get server up
    _server_open(host, port)
    # Start event loop
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


server._auto_stop = False
@react.connect('manager.connections_changed')
def _auto_closer(name):
    if not server._auto_stop:
        return
    for name in manager.get_app_names():
        proxies = manager.get_connections(name)
        if proxies:
            return
    else:
        logging.info('Stopping Flexx event loop.')
        server.stop()


## App functions


def init_notebook():
    """ Initialize the Jupyter notebook by injecting the necessary CSS
    and JS into the browser.
    """
    
    from IPython.display import display, Javascript, HTML
    
    # todo: in exported notebooks, the code display divs take up space?
    def my_send_command(command):
        display(Javascript('flexx.command(%r);' % command))
    
    # Create default session and monkey-patch it
    # Not very pretty, but this keeps notebook logic confined to this module/function.
    proxy = manager.get_default_proxy()
    if hasattr(proxy, '_original_send_command'):
        display(HTML("<i>Flexx already loaded</i>"))
        return  # Don't inject twice
    else:
        proxy._original_send_command = proxy._send_command
        proxy._send_command = my_send_command
        try:
            proxy.use_asset('phosphor-all.js')
            proxy.use_asset('flexx-ui.css')
            proxy.use_asset('flexx-ui.js')
        except IndexError:
            pass  # Ok if it fails; assets can be loaded dynamically.
    
    # Open server - we only use websocket for JS-to-Py communication
    _server_open()
    host, port = server.serving_at
    all_css, all_js = proxy.get_all_css_and_js()
    
    # Compose HTML to inject
    url = 'ws://%s:%i/%s/ws' % (host, port, proxy.app_name)
    t = "<i>Injecting Flexx JS and CSS</i>"
    t += "<style>\n%s\n</style>\n" % all_css
    t += "<script>\n%s\n</script>" % all_js
    t += "<script>flexx.ws_url=%r; flexx.is_notebook=true; flexx.init();</script>" % url
    
    display(HTML(t))


def serve(cls):
    """ Serve the given Pair class as a web app. Can be used as a decorator.
    
    This registers the given class with the internal app manager. The
    app can be loaded via 'http://hostname:port/classname'.
    
    Arguments:
        cls (Pair): a subclass of ``app.Pair`` (or ``ui.Widget``).
    
    Returns:
        cls: The given class.
    """
    # Note: this talks to the manager; it has nothing to do with the server
    assert isinstance(cls, type) and issubclass(cls, Pair)
    manager.register_app_class(cls)
    return cls


def launch(cls, runtime='xul', **runtime_kwargs):
    """ Launch the given Pair class as a desktop app in the given runtime.
    
    Arguments:
        cls (type, str): a subclass of ``app.Pair`` (or ``ui.Widget`). If this 
            is a string, it simply calls ``webruntime.launch()``.
        runtime (str): the runtime to launch the application in. Default 'xul'.
        runtime_kwargs: kwargs to pass to the ``webruntime.launch`` function.
    
    Returns:
        app (Pair): an instance of the given class.
    """
    if isinstance(cls, str):
        return webruntime.launch(cls, runtime, **runtime_kwargs)
    if not (isinstance(cls, type) and issubclass(cls, Pair)):
        raise ValueError('runtime must be a string or Pair subclass.')
    
    # Create session
    serve(cls)
    proxy = manager.create_session(cls.__name__)
    
    # Launch web runtime, the server will wait for the connection
    _server_open()
    host, port = server.serving_at
    if runtime == 'nodejs':
        all_js = proxy.get_all_css_and_js()[1]
        proxy._runtime = launch('http://%s:%i/%s/' % (host, port, proxy.app_name), 
                                runtime=runtime, code=all_js)
    else:
        proxy._runtime = launch('http://%s:%i/%s/?session_id=%s' % (host, port, proxy.app_name, proxy.id), 
                                runtime=runtime, **runtime_kwargs)
    
    return proxy.app


def export(cls, filename=None, single=True):
    """ Export the given Pair class to an HTML document.
    
    Arguments:
        cls (Pair): a subclass of ``app.Pair`` (or ``ui.Widget``).
        filename (str, optional): Path to write the HTML document to.
            If not given or None, will return the html as a string.
        single (bool): If True, will include all JS and CSS dependencies
            in the HTML page. If False, you want to export all assets
            using ``app.assets.export(dirname)``.
    
    Returns:
        html (str): The resulting html. If a filename was specified
        this returns None.
    """
    if not (isinstance(cls, type) and issubclass(cls, Pair)):
        raise ValueError('runtime must be a string or Pair subclass.')
    
    # Create session
    serve(cls)
    proxy = manager.create_session(cls.__name__)
    
    # Make fake connection using exporter object
    exporter = ExporterWebSocketDummy()
    manager.connect_client(exporter, proxy.app_name, proxy.id)
    
    # Clean up again
    manager.disconnect_client(proxy)
    
    # Get HTML - this may be good enough
    html = proxy.get_page_for_export(exporter._commands, single)
    if filename is None:
        return html
    
    # Save to file
    if filename.startswith('~'):
        filename = os.path.expanduser(filename)
    open(filename, 'wt', encoding='utf-8').write(html)
    print('Exported app to %r' % filename)


class ExporterWebSocketDummy(object):
    """ Object that can be used by an app inplace of the websocket to
    export apps to standalone HTML. The object tracks the commands send
    by the app, so that these can be re-played in the exported document.
    """
    close_code = None
    
    def __init__(self):
        self._commands = []
        # todo: make icon and title work
        #self.command('ICON %s.ico' % proxy.id)
        #self.command('TITLE %s' % proxy._runtime_kwargs.get('title', 'Exported flexx app'))
    
    def command(self, cmd):
        self._commands.append(cmd)
