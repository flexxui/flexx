"""
High level code related to the server that provides a mainloop and
serves the pages and websocket.
"""

import sys

import asyncio

from ..event import _loop
from .. import config
from . import logger


# There is always a single current server (except initially there is None)
_current_server = None


def create_server(host=None, port=None, loop=None, backend='tornado',
                  **server_kwargs):
    """
    Create a new server object. This is automatically called; users generally
    don't need this, unless they want to explicitly specify host/port,
    create a fresh server in testing scenarios, or run Flexx in a thread.

    Flexx uses the notion of a single current server object. This function
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
        loop: A fresh (asyncio) event loop, default None (use current).
        backend (str): Stub argument; only Tornado is currently supported.
        **server_kwargs: keyword arguments passed to the server constructor.

    Returns:
        AbstractServer: The server object, see ``current_server()``.
    """

    global _current_server
    # Handle defaults
    if host is None:
        host = config.hostname
    if port is None:
        port = config.port
    # Stop old server
    if _current_server:
        _current_server.close()
    # Start hosting
    backend = backend.lower()
    if backend == 'tornado':
        # Lazy load tornado, so that we can use anything we want there without
        # preventing other parts of flexx.app from using *this* module.
        from ._tornadoserver import TornadoServer  # noqa - circular dependency
        _current_server = TornadoServer(host, port, loop, **server_kwargs)
    elif backend == 'flask':
        # Lazy load flask
        from ._flaskserver import FlaskServer
        _current_server = FlaskServer(host, port, loop, **server_kwargs)
    else:
        raise RuntimeError('Flexx server can only run on Tornado and Flask (for now).')
    assert isinstance(_current_server, AbstractServer)
    return _current_server


def current_server(create=True, **server_kwargs):
    """
    Get the current server object. Creates a server if there is none
    and the ``create`` arg is True. Currently, this is always a
    TornadoServer object, which has properties:

    * serving: a tuple ``(hostname, port)`` specifying the location
      being served (or ``None`` if the server is closed).
    * protocol: the protocol (e.g. "http") being used.
    * app: the ``tornado.web.Application`` instance
    * server: the ``tornado.httpserver.HttpServer`` instance

    """
    if create and not _current_server:
        create_server(**server_kwargs)
    return _current_server


## Server class


async def keep_awake():
    # This is to wake Python up from time to time to allow interruption
    # See #529, and e.g. Hypercorn's run() implementation.
    # Stricly speaking only required on Windows.
    while True:
        await asyncio.sleep(0.2)


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

    def __init__(self, host, port, loop=None, **kwargs):
        # First off, create new event loop and integrate event.loop
        if sys.version_info > (3, 8) and sys.platform.startswith('win'):
            # watch out: this resets any previous set_event_loop
            # Please add comment: What is this used for??
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy()) 
        if loop is None:
            self._loop = asyncio.get_event_loop()
        else:
            assert isinstance(loop, asyncio.AbstractEventLoop)
            self._loop = loop
        asyncio.set_event_loop(self._loop)
        _loop.loop.integrate(self._loop, reset=False)

        self._serving = None
        if host is not False:
            self._open(host, port, **kwargs)
            assert self._serving  # Check that subclass set private variable

    @property
    def _running(self):
        return self._loop.is_running()

    def start(self):
        """ Start the event loop. """
        if not self._serving:
            raise RuntimeError('Cannot start a closed or non-serving server!')
        if self._running:
            raise RuntimeError('Cannot start a running server.')
        if asyncio.get_event_loop() is not self._loop:
            raise RuntimeError('Can only start server in same thread that created it.')
        logger.info('Starting Flexx event loop.')
        # Make use of the semi-standard defined by IPython to determine
        # if the ioloop is "hijacked" (e.g. in Pyzo).
        if not getattr(self._loop, '_in_event_loop', False):
            poller = self._loop.create_task(keep_awake())
            try:
                self._loop.run_forever()
            except KeyboardInterrupt:
                logger.info('Flexx event loop interrupted.')
            except TypeError as err:
                if "close() takes 1 positional argument but 3 were given" in str(err):
                    # This is weird - I looked into this but this does not seem to
                    # originate from Flexx, could this be a bug in CPython?
                    logger.info('Interrupted Flexx event loop.')
                else:
                    raise
            poller.cancel()

    def stop(self):
        """ Stop the event loop. This does not close the connection; the server
        can be restarted. Thread safe. """
        logger.info('Stopping Flexx event loop.')
        self._loop.call_soon_threadsafe(self._loop.stop)

    def close(self):
        """ Close the connection. A closed server cannot be used again. """
        if self._running:
            raise RuntimeError('Cannot close a running server; need to stop first.')
        self._serving = None
        self._close()
        # self._loop.close()

    def _open(self, host, port, **kwargs):
        raise NotImplementedError()

    def _close(self):
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
