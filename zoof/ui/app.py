""" Definition of App class and the app manager.

What one process does
---------------------

In zoof.io, each server process hosts on a single URL (domain+port).
But can serve multiple applications via different paths.

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
of the comminication will go. There is thus one websocket per
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

"""

import inspect

import tornado.ioloop
import tornado.web

from ..webruntime.icon import Icon  # todo: move to util
from zoof.webruntime import launch

# Create/get the tornado event loop
_tornado_loop = tornado.ioloop.IOLoop.instance()

# The tornado server, started on start()
_tornado_app = None


class AppManager(object):
    """ There is one AppManager class (in zoof.ui.app.manager). It's
    purpose is to manage the application classes and instances. It is
    mostly used internally, but advanced users may use it too.
    """
    
    def __init__(self):
        self._apps = {}  # name -> (AppClass, pending, connected)
    
    def register_app_class(self, app_class):
        """ Register an application by its class
        
        Applications are identified by the ``__name__`` attribute of
        the class. The given class must inherit from ``App``.
        
        After registering a class, it becomes possible to connect to 
        "http://address:port/ClassName". 
        """
        assert isinstance(app_class, type) and issubclass(app_class, App)
        name = app_class.__name__
        if name in self._apps:
            raise ValueError('App with name %r already registered' % name)
        self._apps[name] = app_class, [], []
    
    def _add_app_instance(self, app):
        """ Add an app instance as a pending app. User internally.
        Friend method of the App class.
        """
        assert isinstance(app, App)
        name = app.__class__.__name__
        if name not in self._apps:
            self.register_app_class(app.__class__)
        cls, pending, connected = self._apps[name]
        if not isinstance(app, cls):
            raise RuntimeError('Given app is not an instance of corresponding '
                               'registerered class.')
        if app.status == App.STATUS.PENDING:
            assert app not in pending
            pending.append(app)
        else:
            raise RuntimeError('Cannot add app instances that are/were '
                               'already connected')
    
    def get_pendig_app(self, name):
        """ Get an app instance for the given app name
        
        The returned app is a "pending" app, which implies that it is
        not yet connected. It may already exist before this function
        is called. Used in start() to associate a runtime object.
        """
        # todo: remove app instance when disconnected
        cls, pending, connected = self._apps[name]
        if pending:
            return pending[0]
        else:
            app = cls()  # instantiation adds to pending via add_app_instance
            return app
    
    def connect_an_app(self, name, ws):
        """ Connect a pending app instance
        
        Called by the websocket object upon connecting, thus initiating
        the application.
        """
        cls, pending, connected = self._apps[name]
        # Get app (from pending if possible)
        if not pending:
            cls()  # create class, instance ends up in pending
        app = pending.pop(0)
        # Add app to connected, set ws
        assert app.status == app.STATUS.PENDING
        connected.append(app)
        app._ws = ws
        # The app can now be used
        ws.command('ICON %s.ico' % app.id)
        ws.command('TITLE %s' % app._config.title)
        app.init()
        return app
    
    def has_app_name(self, name):
        """ Returns True if name is a registered appliciation name
        """
        return name in self._apps.keys()
    
    def get_app_names(self):
        """ Get a list of registered application names
        """
        return list(self._apps.keys())
    
    def get_app_by_id(self, name, id):
        """ Get app by name and id
        """
        cls, pending, connected = self._apps[name]
        for app in pending:
            if app.id == id:
                return app
        for app in connected:
            if app.id == id:
                return app

# Create app manager object
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


def run(runtime='xul', host='localhost', port=None):
    """ Start the user interface
    
    This will do a couple of things:
    
    * All subclasses of App in the caller namespace are registered as apps.
    * The server is started for UI runtimes to connect to.
    * If specified, a runtime is launched for each application class.
    * The even-loop is started.
    
    This function generally does not return until the application is
    stopped, although it will try to behave nicely in interactive
    environments (e.g. IEP, Spyder, IPython notebook), so the caller
    should take into account that the function may return emmidiately.
    
    """
    # todo: make it work in IPython (should be easy since its tornnado too
    # todo: allow ioloop already running (e.g. integration with ipython)
    
    global _tornado_app 
    
    # Check that its not already running
    if _tornado_app is not None:
        raise RuntimeError('zoof.ui eventloop already running')
    
    # Detect App classes in caller namespace
    app_names = manager.get_app_names()
    frame = inspect.currentframe()
    for ob in frame.f_back.f_locals.values():
        if isinstance(ob, type) and issubclass(ob, App):
            #_app_classes.append(ob)
            if ob.__name__ not in app_names:
                manager.register_app_class(ob)
                print('found', ob.__name__)
    
    # Create server
    from .serve import ZoofTornadoApplication
    _tornado_app = ZoofTornadoApplication()
    
    # Start server (find free port number if port not given)
    if port is not None:
        _tornado_app.listen(port, host)
    else:
        for i in range(100):
            port = port_hash('zoof+%i' % i)
            try:
                _tornado_app.listen(port, host)
                break
            except OSError:
                pass  # address already in use
        else:
            raise RuntimeError('Could not bind to free address')    
    
    # Notify address, so its easy to e.g. copy and paste in the browser
    print('Serving apps at http://%s:%i/' % (host, port))
    
    # Launch runtime for each app
    if runtime:
        for name in manager.get_app_names():
            # We get an app instance and associate the runtime with it. 
            # We assume that the runtime will be the first to connect, and thus
            # pick up this app instance. But this is in no way guaranteed.
            # todo: guarante that runtime connects to exactlty this app
            app = manager.get_pendig_app(name)
            icon = app._config.icon
            icon = icon if icon.image_sizes() else None
            app._runtime = launch('http://localhost:%i/%s/' % (port, name), 
                                  runtime=runtime, 
                                  size=app.config.size,
                                  icon=icon, title=app.config.title)
    
    # Start event loop
    _tornado_loop.start()


def stop():
    """ Stop the event loop
    """
    _tornado_loop.stop()


def process_events():
    """ Process events
    
    Call this to keep the application working while running in a loop.
    """
    _tornado_loop.run_sync(lambda x=None: None)


def call_later(delay, callback, *args, **kwargs):
    """ Call the given callback after delay seconds. If delay is zero, 
    call in the next event loop iteration.
    """
    if delay <= 0:
        _tornado_loop.add_callback(callback, *args, **kwargs)
    else:
        _tornado_loop.call_later(delay, callback, *args, **kwargs)

# todo: move to ..util
def create_enum(*members):
    """ Create an enum type from given string arguments.
    """
    assert all([isinstance(m, str) for m in members])
    enums = dict([(s, s) for s in members])
    return type('Enum', (), enums)


class BaseWidget(object):
    
    def __init__(self, parent):
        self._parent = None
        self._children = []
        self._set_parent(parent)
    
    @property
    def parent(self):
        return self._parent
    
    def _set_parent(self, new_parent):
        old_parent = self._parent
        if old_parent is not None:
            while self in old_parent._children:
                old_parent._children.remove(self)
        if new_parent is not None:
            new_parent._children.append(self)
        self._parent = new_parent
    
    @property
    def children(self):
        return list(self._children)

# In tk, tk.Tk() creates the main window, further windows should be
# created with tk.TopLevel()
# In wx, a Frame is the toplevel window
# In Fltk a Frame can be toplevel or not


class App(BaseWidget):
    """ Base application object
    
    A subclass of the App class represents an application, and also its
    main window.
    
    Subclass this class to implement for a new application. One instance
    of this class will be created for each connection. Therefore, any
    data should be stored on the application object; avoid global data.
    """
    
    icon = None  # todo: how to distinguish this class attr from an instance attr?
    # Maybe we need an AppClass class? for stuff that;s equal for each app instance?
    
    STATUS = create_enum('PENDING', 'CONNECTED', 'CLOSED')
    
    class Config(object):
        """ Config(title='Zoof app', icon=None, size=(640, 480))
        
        args:
            title (str): the window title
            icon (str, Icon): the window icon
            size (tuple): the wise (width, height) of the window. Cannot
                be applied in browser windows.
        """
        
        def __init__(self, title='Zoof app', icon=None, size=(640, 480)):
            self.title = title
            self.icon = Icon()
            if icon:
                self.icon.read(icon)
            self.size = size
        
        def __call__(self, app):
            app._config = self
            return app
    
    _config = Config()  # Set default config
    
    def __init__(self):
        BaseWidget.__init__(self, None)
        # Init websocket, will be set when a connection is made
        self._ws = None
        # Init runtime that is connected with this app instance
        self._runtime = None
        
        # Init
        self._widget_counter = 0
        
        # Register this app instance
        manager._add_app_instance(self)
        print('Instantiate app %s' % self.__class__.__name__)
    
    def __repr__(self):
        s = self.status.lower()
        return '<App %r (%s) at 0x%x>' % (self.__class__.__name__, s, id(self))
    
    @property
    def config(self):
        """ The app configuration. Setting the configuration after
        app instantiation has no effect; this represents the config with 
        which the app was created.
        """
        return self._config
    
    @property
    def name(self):
        """ The name of the app.
        """
        return self.__class__.__name__
    
    @property
    def id(self):
        """ The id of this app as a string
        """
        return '%x' % id(self)
    
    def init(self):
        """ Override this method to initialize the application
        
        It gets called right after the connection with the client has
        been made. This is where you want to create your widgets.
        """
        pass
    
    def close(self):
        """ Close the runtime, if possible
        """
        # todo: close via JS
        if self._runtime:
            self._runtime.close()
    
    @property
    def status(self):
        """ The status of this application. Can be PENDING, CONNECTED or
        CLOSED. See App.STATUS enum.
        """
        # todo: is this how we want to do enums throughout?
        if self._ws is None:
            return self.STATUS.PENDING  # not connected yet
        elif self._ws.close_code is None:
            return self.STATUS.CONNECTED  # alive and kicking
        else:
            return self.STATUS.CLOSED  # connection closed
    
    @property
    def parent(self):
        """ For compatibility with widgets. The parent of an App is
        always None.
        """
        return None
    
    def _exec(self, code):
        """ Like eval, but without returning the result value.
        """
        if self._ws is None:
            raise RuntimeError('App not connected')
        self._ws.command('EXEC ' + code)
    
    def eval(self, code):
        """ Evaluate the given JavaScript code in the client
        
        Intended for use during development and debugging. Deployable
        code should avoid making use of this function.
        """
        if self._ws is None:
            raise RuntimeError('App not connected')
        self._ws.command('EVAL ' + code)
    

class DefaultApp(App):
    pass

