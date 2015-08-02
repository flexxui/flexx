""" Definition of App class and the app manager.

What one process does
---------------------

In flexx.ui, each server process hosts on a single URL (domain+port),
but can serve multiple applications via different paths.

Each process uses one tornado IOLoop (the default one), and exactly one
Tornado Application object.

Applications
------------

Developers create application by implementing an App class. One instance
of this class is instantiated per connection. Multiple apps can be
hosted from the same process simply be specifying more App classes.
To connect to the application `MyApp`, you should connect to 
"http://domain:port/MyApp".

Each connection features a bidirectional websocket through which most
of the communication will go. There is thus one websocket per
application instance. Per application instance, multiple windows
can be opened (via JS ``window.open()``). These windows shall be
controlled via the websocket of the main window.

Making things simple
--------------------

To allow easy access to an app instance during an interactive session,
developers can instantiate a class in their main script. This instance
will be used by the first connection that is made. If two instances
are created, these would be used by the first two connections.

We may allow not specifying an App class at all, in which case a default
App is used (not yet implemented/decided).

How it works in the notebook
----------------------------

In the IPython/Jupyter notebook, the user needs to run ``run()`` (or
something else?) which will inject JS and CSS into the browser. Then,
for each widget that gets repr-ed via ``_repr_html_`` first a container
DOM element is created, in which the widget is displayed.

"""

import os
import time
import inspect
import logging

import tornado.ioloop
import tornado.web

from ..util.icon import Icon
from ..webruntime import launch

from .clientcode import clientCode, Exporter # global client code
from .serialize import serializer
from .pair import Pair


# Create/get the tornado event loop
_tornado_loop = tornado.ioloop.IOLoop.instance()

# The tornado server, started on start()
_tornado_app = None


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
            runtime = 'notebook' if is_notebook else 'browser'  # todo: what runtime?
            proxy = Proxy('__default__', runtime, title='Flexx app')
            pending.append(proxy)
            return proxy
    
    def add_pending_proxy_instance(self, proxy):
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
    
    def connect_client(self, ws, name, app_id=None):
        """ Connect an incoming client connection to a proxy object
        
        Called by the websocket object upon connecting, thus initiating
        the application. The connection can be for the default app, for
        a pending app, or for a fresh app (external connection).
        """
        
        print('connecting', name, app_id)
        
        cls, pending, connected = self._proxies[name]
        
        if name == '__default__':
            if pending:
                proxy = pending.pop(-1)
            else:
                proxy = Proxy(name, runtime=None)
        
        elif not app_id:
            # Create a fresh proxy - there already is a runtime
            proxy = Proxy(cls.__name__, runtime=None)
            app = cls(_proxy=proxy)
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


# Create global app manager object
manager = AppManager()


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


def init_server(host='localhost', port=None):
    global _tornado_app 
    
    # Check that its not already running
    if _tornado_app is not None:
        return
        #raise RuntimeError('flexx.ui server already created')
    
    # Create server
    from .serve import FlexxTornadoApplication
    _tornado_app = FlexxTornadoApplication()
    
    # Start server (find free port number if port not given)
    if port is not None:
        _tornado_app.listen(port, host)
    else:
        for i in range(100):
            port = port_hash('flexx+%i' % i)
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


# todo: ui.run looks weird in IPython. Maybe ui.load() or start()
def run():  # (runtime='xul', host='localhost', port=None):
    """ Start the event loop. This will do a couple of things:
    
    * All subclasses of App in the caller namespace are registered as apps.
    * The server is started for UI runtimes to connect to.
    * If specified, a runtime is launched for each application class.
    * The even-loop is started.
    
    This function generally does not return until the application is
    stopped, although it will try to behave nicely in interactive
    environments (e.g. IEP, Spyder, IPython notebook), so the caller
    should take into account that the function may return emmidiately.
    """
    # Get server up
    init_server()
    # Start event loop
    if not (hasattr(_tornado_loop, '_running') and _tornado_loop._running):
        _tornado_loop.start()
    return JupyterChecker()

is_notebook = False

class JupyterChecker(object):
    """ This gets returned by run(), so that in the IPython notebook
    _repr_html_() gets called. When this happens, we know we are in the
    Jupyter notebook, or at least in something that can display html.
    In the HTML that we then produce, we put the whole flexx library.
    """
    def _repr_html_(self):
        global is_notebook
        from IPython.display import display, Javascript, HTML
        if is_notebook:
            return "<i>Flexx already loaded</i>"  # Don't inject twice
        is_notebook = True
        
        host, port = _tornado_app.serving_at
        #name = app.app_name + '-' + app.id
        name = '__default__'
        url = 'ws://%s:%i/%s/ws' % (host, port, name)
        t = "Injecting JS/CSS"
        t += "<style>\n%s\n</style>\n" % clientCode.get_css()
        t += "<script>\n%s\n</script>" % clientCode.get_js()
        t += "<script>flexx.ws_url=%r; flexx.is_notebook=true; flexx.init();</script>" % url
        
        #return t + '<i>Flexx is ready to go</i>'
        display(HTML(t))
        return '<i>Flexx is ready to go</i>'


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
        _tornado_loop.call_later(delay, callback, *args, **kwargs)

# todo: move to ..util?
def create_enum(*members):
    """ Create an enum type from given string arguments.
    """
    assert all([isinstance(m, str) for m in members])
    enums = dict([(s, s) for s in members])
    return type('Enum', (), enums)


def make_app(cls=None, **kwargs):
    """ Mark a Pair class as an app, to be used as a class decorator
    
    Does three things:
    
    * The class is registered as an app, so that clients (incoming
      connections) can load the app.
    * Adds a ``launch()`` function to the class to easily create an app
      instance.
    * adds ``_IS_APP`` attribute to the class with value ``True`` (used
      internally).
    
    Parameters for the launch function:
      runtime (str): the web runtime to launch the app in. Default
      'xul'. kwargs: combined with the kwargs given to the ``app``
        decorator, these are used to initialize signal values.
      
    """
    kwargs1 = kwargs
    
    def _make_app(cls):
        
        def launch(runtime='xul', **kwargs):
            """ Launch an instance of this app in the specified runtime.
            """
            # Get final kwargs list
            d = {}
            d.update(kwargs1)
            d.update(kwargs)
            # Instantiate widget with a fresh client object
            proxy = Proxy(cls.__name__, runtime, **d)
            app = cls(_proxy=proxy)
            proxy._set_pair_instance(app)
            return app
        
        manager.register_app_class(cls)
        cls.launch = launch
        cls._IS_APP = True  # Mark the class as an app
        return cls
    
    if cls is None:
        return _make_app
    else:
        return _make_app(cls)


# todo: this does not work well with creating apps from scratch yet; see run_python_in_node.py example
class Proxy(object):
    """ A proxy between Python and the client runtime

    This class is basically a wrapper for the app widget, the web runtime,
    and the websocket instance that connects to it.
    """
    
    STATUS = create_enum('PENDING', 'CONNECTED', 'CLOSED')
    
    def __init__(self, app_name, runtime=None, **runtime_kwargs):
        # Note: to avoid circular references, do not store the app instance!
        
        self._app_name = app_name
        
        # Init runtime object (the runtime argument is a string)
        self._runtime = None
        
        # Init websocket, will be set when a connection is made
        self._ws = None
        
        # Unless app_name is __default__, the proxy will have a Pair instance
        self._pair = None
        
        # Object to manage the client code (JS/CSS/HTML)
        self._known_pair_classes = set()
        for cls in clientCode.get_defined_pair_classes():
            self._known_pair_classes.add(cls)
        
        # While the client is not connected, we keep a queue of
        # commands, which are send to the client as soon as it connects
        self._pending_commands = []
        
        if runtime:
            self._launch_runtime(runtime, **runtime_kwargs)
    
    @property
    def id(self):
        """ The unique identifier of this app as a string. Used to
        connect a runtime to a specific client.
        """
        return '%x' % id(self)
    
    @property
    def app_name(self):
        """ The name of the application that this proxy represents.
        """
        return self._app_name
    
    def __repr__(self):
        s = self.status.lower()
        return '<Proxy for %r (%s) at 0x%x>' % (self.app_name, s, id(self))
    
    def _launch_runtime(self, runtime, **runtime_kwargs):
        
        # Register the instance at the manager
        manager.add_pending_proxy_instance(self)
        
        if runtime == '<export>':
            self._ws = Exporter(self)
        elif runtime == 'notebook':
            pass
        elif runtime:
            init_server()
            host, port = _tornado_app.serving_at
            # We associate the runtime with this specific app instance by
            # including the app id to the url. In this way, it is pretty
            # much guaranteed that the runtime will connect to *this* app.
            name = self.app_name
            if name != '__default__':
                name += '-' + self.id
            if runtime == 'nodejs':
                self._runtime = launch('http://%s:%i/%s/' % (host, port, name), 
                                       runtime=runtime, code=clientCode.get_js())
            else:
                self._runtime = launch('http://%s:%i/%s/' % (host, port, name), 
                                       runtime=runtime, **runtime_kwargs)
        
        print('Instantiate app client %s' % self.app_name)
    
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
    
    def close(self):
        """ Close the runtime, if possible
        """
        # todo: close via JS
        if self._runtime:
            self._runtime.close()
        if self._pair:
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
        # todo: do we use this somewhere? It should 
        """ Register the given class. If already registered, this function
        does nothing.
        """
        if not (isinstance(cls, type) and issubclass(cls, Pair)):
            raise ValueError('Not a Pair class')
        
        if cls in self._known_pair_classes:
            return
        
        # Make sure the base classes are defined first
        for cls2 in cls.mro()[1:]:
            if not issubclass(cls2, Pair):  # True if cls2 is *the* Pair class
                break
            if cls2 not in self._known_pair_classes:
                self.register_pair_class(cls2)
        
        # Register
        self._known_pair_classes.add(cls)
        
        # Define class
        print('Dynamically defining class!', cls)
        js = cls.get_js()
        css = cls.get_css()
        self._send_command('DEFINE-JS ' + js)
        if css.strip():
            self._send_command('DEFINE-CSS ' + css)
    
    def _send_command(self, command):
        """ Send the command, add to pending queue, or error when closed.
        """
        if self.status == self.STATUS.CONNECTED:
            if is_notebook:
                # In the notebook, we send commands via a JS display, so that
                # they are also executed when the notebook is exported
                from IPython.display import display, Javascript
                display(Javascript('flexx.command(%r);' % command))
            else:
                self._ws.command(command)
        elif self.status == self.STATUS.PENDING:
            self._pending_commands.append(command)
        else:
            raise RuntimeError('Cannot send commands; app is closed') 
    
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
            _, id, signal_name, txt = command.split(' ', 3)
            ob = Pair._instances.get(id, None)
            if ob is not None:
                # Note that this will again sync with JS, but it stops there:
                # eventual synchronity
                #print('setting signal from js:', signal_name)
                signal = getattr(ob, signal_name)
                value = serializer.loads(txt)
                signal._set(value)
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
    
    @classmethod
    def export(cls, filename=None):
        """ Classmethod to export the app to HTML
        
        This will instantiate an app object, capture all commands that
        it produces in init(), and stores this in a standalone HTML
        document specified by filename.
        """
        app = cls(runtime='<export>')
        if filename is None:
            return app._ws.to_html()
        else:
            return app._ws.write_html(filename)
