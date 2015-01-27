""" Definition of App class and the app manager.

In zoof.ui, an application is defined by an App class. One instance of
this class is instantiated per connection. Further, multiple apps can
be hosted from the same process simply be specifying more App classes.

For simplicity, developers can instantiate the class in their main
script, and this instance will be used for the first connection that
is made.

Further, we may allow not specifying an App class at all, in which case
a default App is used (not yet implemented).

"""

import inspect

import tornado.ioloop
import tornado.web

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
        if app.status == 0:
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
        if pending:
            app = pending.pop(0)
        else:
            app = cls()
        # Add app to connected, set ws
        connected.append(app)
        app._ws = ws
        # Create all widgets associates with app
        # todo: use children
        for key in dir(app):
            if not key.startswith('__'):
                ob = getattr(app, key)
                if ob.__class__.__name__ == 'Button':
                #if isinstance(ob, Widget):
                    ob._create()
    
    def has_app(self, name):
        """ Returns True of name is a registered applciation name
        """
        return name in self._apps.keys()
    
    def get_app_names(self):
        """ Get a list of registered application names
        """
        return list(self._apps.keys())

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
    from .serve import WSHandler, MainHandler
    _tornado_app = tornado.web.Application([(r"/(.*)/ws", WSHandler), 
                                            (r"/(.*)", MainHandler), ])
    
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
            app._runtime = launch('http://localhost:%i/%s' % (port, name), runtime)
    
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



class App(object):
    """ Base application object
    
    Subclass this class to create a defintion for a new application.
    An instance of this class will be created for each connection.
    """
    
    def __init__(self):
        #instance_list = App._instances.setdefault(self._full_app_name(), [])
        #instance_list.append(self)
        print('Instantiate app %s' % self.__class__.__name__)
        # Init websocket, will be set when a connection is made
        self._ws = None
        
        # Init runtime that is connected with this app instance
        self._runtime = None
        
        manager._add_app_instance(self)
        self.init()
    
    def init(self):
        """ Override this method to initialize the application, e.g. 
        create widgets.
        """
        pass
    
    @property
    def status(self):
        """ The statuse of this application.
        """
        if self._ws is None:
            return 0  # not connected yet
        elif self._ws.close_code is None:
            return 1  # alive and kicking
        else:
            return 2  # connection closed
    
    @property
    def parent(self):
        # Make sure this can never be not None
        return None
    
#     @classmethod
#     def _full_app_name(cls):
#         return cls.__module__ + '.' + cls.__name__
#     
#     @classmethod
#     def instances(cls):
#         return App._instances[cls._full_app_name()]
    
    def eval(self, code):
        if self._ws is None:
            raise RuntimeError('App not connected')
        self._ws.write_message('EVAL ' + code, binary=True)


class DefaultApp(App):
    pass

