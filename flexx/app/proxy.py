"""
Definition of App class and the app manager.
"""

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
        is called to get one.
        
        The default "app" is served at "http://address:port/__default__".
        """
        _, pending, connected = self._proxies['__default__']
        proxies = pending + connected
        if proxies:
            return proxies[-1]
        else:
            runtime = 'notebook' if funcs.is_notebook else 'browser'  # todo: what runtime?
            proxy = Proxy('__default__', runtime, title='Flexx app')
            pending.append(proxy)
            return proxy
    
    def instantiate_proxy(self, name, runtime=None):
        
        # Create proxy. The runtime will be served a page that has the
        # proxy id in it. Upon connecting, the id will be communicated,
        # so we can connect to the correct proxy.
        if name not in self._proxies:
            raise ValueError('Can only instantiate a proxy with a valid app name.')
        
        cls, pending, connected = self._proxies[name]
        
        if name == '__default__':
            xxxx
        
        proxy = Proxy(cls.__name__)
        app = cls(proxy=proxy, container='body')
        proxy._set_pair_instance(app)
        
        pending.append(proxy)
        
        # todo: move this to funcs.export and funcs.launch
        # if runtime is None:
        #     pass
        # elif runtime == 'notebook':
        #     pass
        # elif runtime == '<export>':
        #     proxy._connect_client(Exporter(proxy))
        # elif runtime:
        #     funcs.init_server()
        #     
        #     host, port = funcs._tornado_app.serving_at  # todo: yuk
        #     if runtime == 'nodejs':
        #         all_js = assets.get_all_css_and_js()[1]
        #         self._runtime = funcs.launch('http://%s:%i/%s/' % (host, port, name), 
        #                                      runtime=runtime, code=all_js)
        #     else:
        #         self._runtime = funcs.launch('http://%s:%i/%s/' % (host, port, name), 
        #                                      runtime=runtime, **runtime_kwargs)
        
        logging.debug('Instantiate app client %s' % proxy.app_name)
        return proxy
    
    def connect_client(self, ws, name, app_id):
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
        proxy._connect_client(ws)
        connected.append(proxy)
        self.connections_changed._set(proxy.app_name)
        return proxy  # For the ws
    
    def XXXadd_pending_proxy_instance(self, proxy):
        """ Add an app instance as a pending app. 
        
        This means that the proxy is created from Python and not yet
        connected. A runtime has been launched and we're waiting for
        it to connect.
        """
        assert isinstance(proxy, Proxy)
        assert proxy.app_name in self._proxies
        
        cls, pending, connected = self._proxies[proxy.app_name]
        if proxy.status == Proxy.STATUS.PENDING:
            assert proxy not in pending
            pending.append(proxy)
        else:
            raise RuntimeError('Cannot add proxy instances that are/were '
                               'already connected')
    
    def XXXconnect_client(self, ws, name, app_id=None):
        """ Connect an incoming client connection to a proxy object
        
        Called by the websocket object upon connecting, thus initiating
        the application. The connection can be for the default app, for
        a pending app, or for a fresh app (external connection).
        """
        
        logging.debug('connecting %s %s' %(name, app_id))
        
        cls, pending, connected = self._proxies[name]
        
        if name == '__default__':
            if pending:
                proxy = pending.pop(-1)
            else:
                proxy = Proxy(name, runtime=None)
        
        elif not app_id:
            # Create a fresh proxy - there already is a runtime
            proxy = Proxy(cls.__name__, runtime=None)
            app = cls(proxy=proxy, container='body')
            proxy._set_pair_instance(app)
        else:
            # Search for the app with the specific id
            for proxy in pending:
                if proxy.id == app_id:
                    pending.remove(proxy)
                    break
            else:
                raise RuntimeError('Asked for app id %r, '
                                   'but could not find it' % app_id)
        
        # Add app to connected, set ws
        assert proxy.status == Proxy.STATUS.PENDING
        proxy._connect_client(ws)
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
        """ Get a list of registered application names
        """
        return [name for name in self._proxies.keys()]
    
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
        # Note: to avoid circular references, do not store the app instance!
        
        self.add_asset('index-flexx-id.js', ('window.flexx_session_id = %r;\n' % self.id).encode())
        self.use_asset('flexx-app.js')
        
        self._app_name = app_name
        # self._runtime_kwargs = runtime_kwargs
        
        # Init runtime object (the runtime argument is a string)
        self._runtime = None
        
        # Init websocket, will be set when a connection is made
        self._ws = None
        
        # Unless app_name is __default__, the proxy will have a Pair instance
        self._pair = None
        
        # While the client is not connected, we keep a queue of
        # commands, which are send to the client as soon as it connects
        self._pending_commands = []
        
        # if runtime:
        #     self._launch_runtime(runtime, **runtime_kwargs)
    
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
    
    def __repr__(self):
        s = self.status.lower()
        return '<Proxy for %r (%s) at 0x%x>' % (self.app_name, s, id(self))
    
    # def _launch_runtime(self, runtime, **runtime_kwargs):
    #     
    #     # Register the instance at the manager
    #     manager.add_pending_proxy_instance(self)
    #     
    #     if runtime == '<export>':
    #         self._ws = Exporter(self)
    #     elif runtime == 'notebook':
    #         pass
    #     elif runtime:
    #         funcs.init_server()
    #         
    #         host, port = funcs._tornado_app.serving_at  # todo: yuk
    #         # We associate the runtime with this specific app instance by
    #         # including the app id to the url. In this way, it is pretty
    #         # much guaranteed that the runtime will connect to *this* app.
    #         name = self.app_name
    #         if name != '__default__':
    #             name += '-' + self.id
    #         if runtime == 'nodejs':
    #             all_js = assets.get_all_css_and_js()[1]
    #             self._runtime = funcs.launch('http://%s:%i/%s/' % (host, port, name), 
    #                                          runtime=runtime, code=all_js)
    #         else:
    #             self._runtime = funcs.launch('http://%s:%i/%s/' % (host, port, name), 
    #                                          runtime=runtime, **runtime_kwargs)
    #     
    #     logging.debug('Instantiate app client %s' % self.app_name)
    
    def _connect_client(self, ws):
        assert self._ws is None
        # Set websocket object - this is what changes the status to CONNECTED
        self._ws = ws  
        # todo: re-enable this
        # Set some app specifics
        # self._ws.command('ICON %s.ico' % self.id)
        # self._ws.command('TITLE %s' % self._config.title)
        # Send pending commands
        for command in self._pending_commands:
            self._ws.command(command)
   
    def _set_pair_instance(self, pair):
        assert self._pair is None
        self._pair = pair
        # todo: connect to title change and icon change events
    
    def _set_runtime(self, runtime):
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
    
    def register_pair_class(self, cls):
        self._register_pair_class(cls)  # todo: make this the public
    
    def _send_command(self, command):
        """ Send the command, add to pending queue.
        """
        if self.status == self.STATUS.CONNECTED:
            if funcs.is_notebook:  # todo: yuk
                # In the notebook, we send commands via a JS display, so that
                # they are also executed when the notebook is exported
                from IPython.display import display, Javascript
                display(Javascript('flexx.command(%r);' % command))
            else:
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


class Exporter(object):
    """ Object that can be used by an app inplace of the websocket to
    export apps to standalone HTML. The object tracks the commands send
    by the app, so that these can be re-played in the exported document.
    """
    
    def __init__(self, proxy):
        self._commands = []
        self.close_code = None  # simulate web socket
        
        # todo: how to export icons
        self.command('ICON %s.ico' % proxy.id)
        self.command('TITLE %s' % proxy._runtime_kwargs.get('title', 'Exported flexx app'))
    
    def command(self, cmd):
        self._commands.append(cmd)
    
    def write_html(self, filename, single=True):
        """ Write html document to the given file.
        """
        if filename.startswith('~'):
            filename = os.path.expanduser(filename)
        html = self.to_html(single)
        open(filename, 'wt', encoding='utf-8').write(html)
        print('Exported app to %r' % filename)
    
    def write_dependencies(self, dirname):
        """ Write dependencies to the given dir (if a path to a file
        is given, will write to the same directory as that file). Use
        this if you export using ``single == False``.
        """
        if dirname.startswith('~'):
            dirname = os.path.expanduser(dirname)
        if os.path.isfile(dirname):
            dirname = os.path.dirname(dirname)
        raise NotImplementedError()
        #for fname, content in xxx.get_js_and_css_assets().items():
        #    open(os.path.join(dirname, fname), 'wt', encoding='utf-8').write(content)
    
    def to_html(self, single=True):
        """ Get the HTML string.
        """
        html = assets.get_page_for_export(self._commands, single)
        return html  # todo: minify somewhere ...


from . import funcs  # todo: arg circular import
