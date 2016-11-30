# There is always a single current server (except initially there is None)

from ..event import _loop
from .. import config

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
    # Lazy load tornado, so that we can use anything we want there without
    # preventing other parts of flexx.app from using *this* module.
    from ._tornadoserver import TornadoServer  # noqa - circular dependency
    
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


def current_server(create=True):
    """
    Get the current server object. Creates a server if there is none
    and the ``create`` arg is True. Currently, this is always a
    TornadoServer object, which has properties:
    
    * serving: a tuple ``(hostname, port)`` specifying the location
      being served (or ``None`` if the server is closed).
    * app: the ``tornado.web.Application`` instance
    * loop: the ``tornado.ioloop.IOLoop`` instance
    * server: the ``tornado.httpserver.HttpServer`` instance
    """
    if create and not _current_server:
        create_server()
    return _current_server


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
    server = current_server(False)
    if not server:
        _pending_call_laters.append((delay, callback, args, kwargs))
    else:
        server.call_later(delay, callback, *args, **kwargs)

_pending_call_laters = []

# Integrate the "event-loop" of flexx.event
_loop.loop.integrate(lambda f: call_later(0, f))
