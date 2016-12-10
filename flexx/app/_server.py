"""
High level code related to the server that provides a mainloop and
serves the pages and websocket. Also provides call_later().
"""

from ..event import _loop
from .. import config


# There is always a single current server (except initially there is None)
_current_server = None


def create_server(host=None, port=None, new_loop=False, backend='tornado',
                  **server_kwargs):
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
        **server_kwargs: keyword arguments passed to the server constructor.
    
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
    _current_server = TornadoServer(host, port, new_loop, **server_kwargs)
    assert isinstance(_current_server, AbstractServer)
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


## Server class


class AbstractServer:
    """ This is an attempt to generalize the server, so that in the
    future we may have e.g. a Flask or Pyramid server.
    
    A server must implement this, and use the manager to instantiate,
    connect and disconnect sessions. The assets object must be used to
    server assets to the client.
    
    Arguments:
        host (str): the hostname to serve at
        port (int): the port to serve at. None or 0 mean to autoselect a port.
    """
    
    def __init__(self, host, port, **kwargs):
        self._serving = None
        if host is not False:
            self._open(host, port, **kwargs)
            assert self._serving  # Check that subclass set private variable
        self._running = False
    
    def start(self):
        """ Start the event loop. """
        if not self._serving:
            raise RuntimeError('Cannot start a closed or non-serving server!')
        if self._running:
            raise RuntimeError('Cannot start a running server.')
        self._running = True
        try:
            self._start()
        finally:
            self._running = False
    
    def stop(self):
        """ Stop the event loop. This does not close the connection; the server
        can be restarted. Thread safe. """
        self.call_later(0, self._stop)
    
    def close(self):
        """ Close the connection. A closed server cannot be used again. """
        if self._running:
            raise RuntimeError('Cannot close a running server; need to stop first.')
        self._serving = None
        self._close()
    
    def _open(self, host, port, **kwargs):
        raise NotImplementedError()
    
    def _start(self):
        raise NotImplementedError()
    
    def _stop(self):
        raise NotImplementedError()
    
    def _close(self):
        raise NotImplementedError()
    
    # This method must be implemented directly for performance (its used a lot)
    def call_later(self, delay, callback, *args, **kwargs):
        """ Call a function in a later event loop iteration. """
        raise NotImplementedError()
    
    @property
    def serving(self):
        """ Get a tuple (hostname, port) that is being served.
        Or None if the server is not serving (anymore).
        """
        return self._serving

    @property
    def protocol(self):
        """ Get a string representing served protocol
        """
        raise NotImplementedError
