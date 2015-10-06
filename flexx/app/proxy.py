"""
Definition of App class and the app manager.
"""

import os
import time
import inspect
import logging

from ..util.icon import Icon
from .. import webruntime
from .. import react

from .pair import Pair
from .assetstore import SessionAssets


# todo: rename to SessionManager
class AppManager(object):
    """ Manage apps, or more specifically, the proxy objects.
    
    There is one AppManager class (in ``flexx.pair.manager``). It's
    purpose is to manage the application classes and instances. Intended
    for internal use.
    """
    
    def __init__(self):
        # name -> (PairClass, pending, connected) - lists contain proxies
        self._proxies = {'__default__': (None, [], [])}
    
    def register_app_class(self, cls):
        """ Register a Pair class as being an application.
        
        Applications are identified by the ``__name__`` attribute of
        the class. The given class must inherit from ``Pair``.
        
        After registering a class, it becomes possible to connect to 
        "http://address:port/ClassName". 
        """
        assert isinstance(cls, type) and issubclass(cls, Pair)
        name = cls.__name__
        pending, connected = [], []
        if name in self._proxies and cls is not self._proxies[name][0]:
            oldCls, pending, connected = self._proxies[name]
            logging.warn('Re-registering app class %r' % name)
            #raise ValueError('App with name %r already registered' % name)
        self._proxies[name] = cls, pending, connected
    
    def get_default_proxy(self):
        """ Get the default proxy that is used for interactive use.
        
        When a Pair class is created without a proxy, this method
        is called to get one. The default "app" is served at
        "http://address:port/__default__".
        """
        _, pending, connected = self._proxies['__default__']
        proxies = pending + connected
        if proxies:
            return proxies[-1]
        else:
            proxy = Proxy('__default__')
            pending.append(proxy)
            return proxy
    
    def create_session(self, name):
        """ Create a session for the app with the given name.
        
        Instantiate an app and matching session object corresponding
        to the given name, and return the session. The client should
        be connected via connect_client().
        """
        
        if name not in self._proxies:
            raise ValueError('Can only instantiate a proxy with a valid app name.')
        
        cls, pending, connected = self._proxies[name]
        
        if name == '__default__':
            xxxx
        
        # Proxy and app class need each-other, thus the _set_app()
        proxy = Proxy(cls.__name__)
        app = cls(proxy=proxy, container='body')
        proxy._set_app(app)
        
        # Now wait for the client to connect. The client will be served
        # a page that contains the session_id. Upon connecting, the id
        # will be communicated, so it connects to the correct proxy.
        pending.append(proxy)
        
        logging.debug('Instantiate app client %s' % proxy.app_name)
        return proxy
    
    def connect_client(self, ws, name, app_id):
        """ Connect a client to a session that was previously created.
        """
        logging.debug('connecting %s %s' %(name, app_id))
        cls, pending, connected = self._proxies[name]
        
        # Search for the proxy with the specific id
        for proxy in pending:
            if proxy.id == app_id:
                pending.remove(proxy)
                break
        else:
            raise RuntimeError('Asked for app id %r, but could not find it' % app_id)
    
        # Add app to connected, set ws
        assert proxy.status == Proxy.STATUS.PENDING
        proxy._set_ws(ws)
        connected.append(proxy)
        self.connections_changed._set(proxy.app_name)
        return proxy  # For the ws
    
    def disconnect_client(self, proxy):
        """ Close a connection to a client.
        
        This is called by the websocket when the connection is closed.
        The manager will remove the proxy from the list of connected
        instances.
        """
        cls, pending, connected = self._proxies[proxy.app_name]
        try:
            connected.remove(proxy)
        except ValueError:
            pass
        proxy.close()
        self.connections_changed._set(proxy.app_name)
    
    def has_app_name(self, name):
        """ Returns True if name is a registered appliciation name
        """
        return name in self._proxies.keys()
    
    def get_app_names(self):
        """ Get a list of registered application names (excluding those
        that start with an underscore).
        """
        return [name for name in self._proxies.keys() if not name.startswith('_')]
    
    def get_proxy_by_id(self, name, id):
        """ Get proxy object by name and id
        """
        cls, pending, connected = self._proxies[name]
        for proxy in pending:
            if proxy.id == id:
                return proxy
        for proxy in connected:
            if proxy.id == id:
                return proxy
    
    def get_connections(self, name):
        """ Given an app name, return the proxy connected objects.
        """
        cls, pending, connected = self._proxies[name]
        return list(connected)
    
    @react.source
    def connections_changed(self, name):
        """ Emits the name of the app for which a connection is added
        or removed.
        """
        return str(name)


# Create global app manager object
manager = AppManager()


# todo: find other solution?
def create_enum(*members):
    """ Create an enum type from given string arguments.
    """
    assert all([isinstance(m, str) for m in members])
    enums = dict([(s, s) for s in members])
    return type('Enum', (), enums)
    

# todo: rename to Session
class Proxy(SessionAssets):
    """ A proxy between Python and the client runtime

    This class is basically a wrapper for the app widget, the web runtime,
    and the websocket instance that connects to it.
    """
    
    STATUS = create_enum('PENDING', 'CONNECTED', 'CLOSED')
    
    def __init__(self, app_name):
        super().__init__()
        
        # Init assets
        self.add_asset('index-flexx-id.js', ('window.flexx_session_id = %r;\n' % self.id).encode())
        self.use_asset('flexx-app.js')
        
        self._app_name = app_name  # name of the app, available before the app itself
        self._runtime = None  # init web runtime, will be set when used
        self._ws = None  # init websocket, will be set when a connection is made
        self._pair = None  # unless app_name is __default__, the proxy will have a Pair instance
        
        # While the client is not connected, we keep a queue of
        # commands, which are send to the client as soon as it connects
        self._pending_commands = []
    
    def __repr__(self):
        s = self.status.lower()
        return '<Proxy for %r (%s) at 0x%x>' % (self.app_name, s, id(self))
    
    @property
    def app_name(self):
        """ The name of the application that this proxy represents.
        """
        return self._app_name
    
    @property
    def app(self):
        """ The Pair instance that represents the app. Can be None if this
        is the ``__default__`` app.
        """
        return self._pair
    
    @property
    def runtime(self):
        """ The runtime that is rendering this app instance. Can be
        None if the client is a browser.
        """
        return self._runtime
    
    def _set_ws(self, ws):
        """ A proxy is always first created, so we know what page to
        serve. The client will connect the websocket, and communicate
        the session_id so it can be connected to the correct Session
        via this method
        """
        if self._ws is not None:
            raise RuntimeError('Session is already connected.')
        # Set websocket object - this is what changes the status to CONNECTED
        self._ws = ws  
        # todo: make icon and title work again. Also in exported docs.
        # Set some app specifics
        # self._ws.command('ICON %s.ico' % self.id)
        # self._ws.command('TITLE %s' % self._config.title)
        # Send pending commands
        for command in self._pending_commands:
            self._ws.command(command)
   
    def _set_app(self, pair):
        if self._pair is not None:
            raise RuntimeError('Session already has an associated Model.')
        self._pair = pair
        # todo: connect to title change and icon change events
    
    def _set_runtime(self, runtime):
        if self._runtime is not None:
            raise RuntimeError('Session already has a runtime.')
        self._runtime = runtime
    
    def close(self):
        """ Close the runtime, if possible
        """
        # todo: close via JS
        if self._runtime:
            self._runtime.close()
        if self._pair:
            self._pair.disconnect_signals()
            self._pair = None  # break circular reference
    
    @property
    def status(self):
        """ The status of this proxy. Can be PENDING, CONNECTED or
        CLOSED. See Proxy.STATUS enum.
        """
        # todo: is this how we want to do enums throughout?
        if self._ws is None:
            return self.STATUS.PENDING  # not connected yet
        elif self._ws.close_code is None:
            return self.STATUS.CONNECTED  # alive and kicking
        else:
            return self.STATUS.CLOSED  # connection closed
    
    ## Widget-facing code
    
    def _send_command(self, command):
        """ Send the command, add to pending queue.
        """
        if self.status == self.STATUS.CONNECTED:
            self._ws.command(command)
        elif self.status == self.STATUS.PENDING:
            self._pending_commands.append(command)
        else:
            #raise RuntimeError('Cannot send commands; app is closed')
            logging.warn('Cannot send commands; app is closed')
    
    def _receive_command(self, command):
        """ Received a command from JS.
        """
        if command.startswith('RET '):
            print(command[4:])  # Return value
        elif command.startswith('ERROR '):
            logging.error('JS - ' + command[6:].strip())
        elif command.startswith('WARN '):
            logging.warn('JS - ' + command[5:].strip())
        elif command.startswith('PRINT '):
            print(command[5:].strip())
        elif command.startswith('INFO '):
            logging.info('JS - ' + command[5:].strip())
        elif command.startswith('SIGNAL '):
            # todo: seems weird to deal with here. implement this by registring some handler?
            _, id, esid, signal_name, txt = command.split(' ', 4)
            ob = Pair._instances.get(id, None)
            if ob is not None:
                ob._set_signal_from_js(signal_name, txt, esid)
        else:
            logging.warn('Unknown command received from JS:\n%s' % command)
    
    def _exec(self, code):
        """ Like eval, but without returning the result value.
        """
        self._send_command('EXEC ' + code)
    
    def eval(self, code):
        """ Evaluate the given JavaScript code in the client
        
        Intended for use during development and debugging. Deployable
        code should avoid making use of this function.
        """
        if self._ws is None:
            raise RuntimeError('App not connected')
        self._send_command('EVAL ' + code)
