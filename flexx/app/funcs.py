import os
import time
import inspect
import logging

import tornado.ioloop
import tornado.web

from ..util.icon import Icon
from .. import webruntime
from .. import react

from .pair import Pair
from .proxy import Proxy, manager
from .assetstore import assets

# Create/get the tornado event loop
_tornado_loop = tornado.ioloop.IOLoop.instance()

# The tornado server, started on start()
_tornado_app = None





# todo: move to ..utils
def port_hash(name):
    """ port_hash(name)
    
    Given a string, returns a port number between 49152 and 65535. 
    (2**14 (16384) different posibilities)
    This range is the range for dynamic and/or private ports 
    (ephemeral ports) specified by iana.org.
    The algorithm is deterministic, thus providing a way to map names
    to port numbers.
    
    """
    fac = 0xd2d84a61
    val = 0
    for c in name:
        val += ( val>>3 ) + ( ord(c)*fac )
    val += (val>>3) + (len(name)*fac)
    return 49152 + (val % 2**14)


def init_server(host=None, port=None):
    """ Initialize the server if it is not already running.
    """
    global _tornado_app 
    
    # Check that its not already running
    if _tornado_app is not None:
        return
        #raise RuntimeError('flexx.ui server already created')
    
    # Create server
    from .server import FlexxTornadoApplication
    _tornado_app = FlexxTornadoApplication()
    
    # Get default host and port
    if host is None:
        host = os.getenv('FLEXX_HOSTNAME', 'localhost')
    if port is None:
        port = os.getenv('FLEXX_PORT', None)
    
    # Start server (find free port number if port not given)
    if port is not None:
        port = int(port)
        _tornado_app.listen(port, host)
    else:
        for i in range(100):
            port = port_hash('flexx%i' % i)
            try:
                _tornado_app.listen(port, host)
                break
            except OSError:
                pass  # address already in use
        else:
            raise RuntimeError('Could not bind to free address')    
    
    # Notify address, so its easy to e.g. copy and paste in the browser
    _tornado_app.serving_at = host, port
    print('Serving apps at http://%s:%i/' % (host, port))


def start(host=None, port=None):
    """ Start the server and event loop if not already running.
    
    This function generally does not return until the application is
    stopped, although it will try to behave nicely in interactive
    environments (e.g. Spyder, IEP, Jupyter notebook), so the caller
    should take into account that the function may return immediately.
    
    Arguments:
        host (str): The hostname to serve on. Default 'localhost'. This
            parameter is ignored if the server was already running.
        port (int, str): The port number. If a string is given, it is
            hashed to an ephemeral port number. If not given or None,
            will try a series of ports until one is found that is free.
    """
    # Get server up
    init_server(host, port)
    # Start event loop
    if not (hasattr(_tornado_loop, '_running') and _tornado_loop._running):
        _tornado_loop.start()


def run():
    """ Start the event loop if not already running, for desktop apps.
    
    In contrast to ``start()``, when the server is started this way,
    it will close down when there are no more connections.
    """
    manager._auto_stop = True
    return start()


manager._auto_stop = False
@react.connect('manager.connections_changed')
def _auto_closer(name):
    if not manager._auto_stop:
        return
    for name in manager.get_app_names():
        proxies = manager.get_connections(name)
        if proxies:
            return
    else:
        logging.info('Stopping Flexx event loop.')
        stop()

is_notebook = False

def init_notebook():
    """ Initialize the Jupyter notebook by injecting the necessary CSS
    and JS into the browser.
    """
    
    global is_notebook
    from IPython.display import display, Javascript, HTML
    if is_notebook:
        display(HTML("<i>Flexx already loaded</i>"))
        return  # Don't inject twice
    is_notebook = True
    
    init_server()
    host, port = _tornado_app.serving_at
    all_css, all_js = assets.get_all_css_and_js()
    #name = app.app_name + '-' + app.id
    name = '__default__'
    url = 'ws://%s:%i/%s/ws' % (host, port, name)
    t = "<i>Injecting Flexx JS and CSS</i>"
    t += "<style>\n%s\n</style>\n" % all_css
    t += "<script>\n%s\n</script>" % all_js
    t += "<script>flexx.ws_url=%r; flexx.is_notebook=true; flexx.init();</script>" % url
    
    display(HTML(t))


def stop():
    """ Stop the event loop
    """
    _tornado_loop.stop()

# # todo: this does not work if the event loop is running!
# def process_events():
#     """ Process events
#     
#     Call this to keep the application working while running in a loop.
#     """
#     _tornado_loop.run_sync(lambda x=None: None)


def call_later(delay, callback, *args, **kwargs):
    """ Call the given callback after delay seconds. If delay is zero, 
    call in the next event loop iteration.
    """
    if delay <= 0:
        _tornado_loop.add_callback(callback, *args, **kwargs)
    else:
        _tornado_loop.add_timeout(_tornado_loop.time() + delay, callback, *args, **kwargs)
        #_tornado_loop.call_later(delay, callback, *args, **kwargs)  # v4.0+


# todo: move init_notebook, serve, launch, export to proxy/session?
def serve(cls):
    """ Serve the given Pair class as a web app. Can be used as a decorator.
    
    This registers the given class with the internal app manager. The
    app can be loaded via 'http://hostname:port/classname'.
    
    Arguments:
        cls (Pair): a subclass of ``app.Pair`` (or ``ui.Widget``).
    
    Returns:
        cls: The given class.
    """
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
    assert isinstance(cls, type) and issubclass(cls, Pair)
    serve(cls)
    proxy = manager.instantiate_proxy(cls.__name__)
    
    init_server()
    host, port = _tornado_app.serving_at  # todo: yuk
    if runtime == 'nodejs':
        all_js = proxy.get_all_css_and_js()[1]
        proxy._runtime = launch('http://%s:%i/%s/' % (host, port, proxy.app_name), 
                                runtime=runtime, code=all_js)
    else:
        proxy._runtime = launch('http://%s:%i/%s/?session_id=%s' % (host, port, proxy.app_name, proxy.id), 
                                runtime=runtime, **runtime_kwargs)

    # proxy = Proxy(cls.__name__, runtime, **runtime_kwargs)
    # app = cls(proxy=proxy, container='body')
    # proxy._set_pair_instance(app)
    return proxy.app


def export(cls, filename=None, single=True, deps=True):
    """ Export the given Pair class to an HTML document.
    
    Arguments:
        cls (Pair): a subclass of ``app.Pair`` (or ``ui.Widget``).
        filename (str, optional): Path to write the HTML document to.
            If not given or None, will return the html as a string.
        single (bool): If True, will include all JS and CSS dependencies
            in the HTML page.
        deps (bool): If deps is True, will also export the dependent
            JS and CSS files (in case single is False).
    
    Returns:
        html (str): The resulting html. If a filename was specified
        this returns None.
    """
    assert isinstance(cls, type) and issubclass(cls, Pair)
    serve(cls)
    proxy = Proxy(cls.__name__, '<export>')
    app = cls(proxy=proxy, container='body')
    proxy._set_pair_instance(app)
    if filename is None:
        return proxy._ws.to_html()
    else:
        proxy._ws.write_html(filename, single)
        if deps and not single:
            proxy._ws.write_dependencies(filename)
