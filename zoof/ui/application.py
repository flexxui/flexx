""" Definition of application class
"""

import inspect
#from collections import OrderedDict

import tornado.ioloop
import tornado.web

from .serve import TornadoApplication
from zoof.webruntime import launch

# todo: rename this module to app.py

_tornado_loop = tornado.ioloop.IOLoop.instance()
_tornado_app = None

_app_classes = {}  # name -> class


class AppManager(object):
    
    def __init__(self):
        self._apps = {}  # name -> (AppClass, pending, connected)
    
    def register_app_class(self, app_class):
        assert isinstance(app_class, type) and issubclass(app_class, App)
        name = app_class.__name__
        if name in self._apps:
            raise ValueError('App with name %r already registered' % name)
        self._apps[name] = app_class, [], []
    
    def add_app_instance(self, app):
        assert isinstance(app, App)
        name = app.__class__.__name__
        if name not in self._apps:
            self.register_app_class(app.__class__)
        cls, pending, connected = self._apps[name]
        if not isinstance(app, cls):
            raise RuntimeError('Given app is not an instance of corresponding '
                               'registerered class.')
        if app.status == 0:
            pending.append(app)
        else:
            raise RuntimeError('Cannot add app instances that are/were '
                               'already connected')
    
    def get_pendig_app(self, name):
        # todo: remove app instance when disconnected
        cls, pending, connected = self._apps[name]
        if pending:
            return pending[0]
        else:
            app = cls()  # instantiation adds to pending via add_app_instance
            return app
    
    def connect_an_app(self, name, ws):
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
                if isinstance(ob, Widget):
                    ob._create()
    
    def has_app(self, name):
        return name in self._apps.keys()
    
    def get_app_names(self):
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


def start(runtime=None):
    # todo: prevent already running
    global _tornado_app 
    
    # Detect App classes in caller namespace
    app_names = manager.get_app_names()
    frame = inspect.currentframe()
    for ob in frame.f_back.f_locals.values():
        if isinstance(ob, type) and issubclass(ob, App):
            #_app_classes.append(ob)
            if ob.__name__ not in app_names:
                manager.register_app_class(ob)
                print('found', ob.__name__)
    
    # Set host. localhost is safer
    host = 'localhost'  # or other host name or known ip address.
    
    # Start server
    if _tornado_app is None:
        _tornado_app = TornadoApplication()
        # Find free port number
        for i in range(100):
            port = port_hash('zoof+%i' % i)
            try:
                _tornado_app.listen(port, host)
                break
            except OSError:
                pass  # address already in use
        else:
            raise RuntimeError('Could not bind to free address')    
        
        print('Serving apps at http://%s:%i/' % (host, port))
    
    # Launch runtime for each app
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
    _tornado_loop.stop()


def process_events():
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
    
    # todo: where to store this dict?
    # todo: must these be weakrefs?
    # todo: do we need an app manager?
    _instances = {}  # class -> list of instances
    
    def __init__(self):
        #instance_list = App._instances.setdefault(self._full_app_name(), [])
        #instance_list.append(self)
        print('Instantiate app %s' % self.__class__.__name__)
        # Init websocket, will be set when a connection is made
        self._ws = None
        
        # Init runtime that is connected with this app instance
        self._runtime = None
        
        manager.add_app_instance(self)
        self.init()
    
    def init(self):
        pass
    
    @property
    def status(self):
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


# Register default class
_app_classes['default'] = DefaultApp


# class App(object):
#     """ zoof.ui app. There is only one instance.
#     """
#     
#     def __init__(self, runtime='xul'):
#         # todo: singleton?
#         self._ioloop = tornado.ioloop.IOLoop.instance()
#         
#         self._tornado_app = TornadoApplication()
#         
#         # Set host. localhost is safer
#         host = 'localhost'  # or other host name or known ip address.
#         
#         # Find free port number
#         for i in range(100):
#             port = port_hash('zoof+%i' % i)
#             try:
#                 self._tornado_app.listen(port, host)
#                 break
#             except OSError:
#                 pass  # address already in use
#         else:
#             raise RuntimeError('Could not bind to free address')    
#         
#         self._tornado_app.zoof_port = port
#         self._runtime = launch('http://localhost:%i' % port, runtime)
#     
#     def eval(self, code):
#         self._tornado_app.write_message('EVAL ' + code)
#     
#     def start(self):  # todo: or run()?
#         self._ioloop.start()
#     
#     def stop(self):
#         self._ioloop.stop()
#     
#     def process_events(self):
#         self._ioloop.run_sync(lambda x=None: None)
#     
#     def call_later(self, delay, callback, *args, **kwargs):
#         """ Call the given callback after delay seconds. If delay is zero, 
#         call in the next event loop iteration.
#         """
#         if delay <= 0:
#             self._ioloop.add_callback(callback, *args, **kwargs)
#         else:
#             self._ioloop.call_later(delay, callback, *args, **kwargs)



class NativeElement(object):
    
    def __init__(self, id):
        t = 'document.getElementById("{id}").innerHTML = "{text}"'
        # ... get __dir__ from JS and allow live inspection of DOM elements
        # That would be great for debugging ...


class Widget(object):
    _counter = 0
    def __init__(self, parent):
        self._parent = parent
        
        #
    
    def _create(self, app):
        
        if self._parent is None:
            win = self._app._new_window()


class Label(Widget):
    pass

class Button(Widget):
    _TEMPLATE = """
        var e = document.createElement("button");
        e.id = '{id}';
        e.innerHTML = '{text}'
        document.body.appendChild(e);
        """
    
    def __init__(self, parent, text='Click me'):
        Widget._counter += 1
        self._parent = parent
        self._id = 'but%i' % Widget._counter
        self._text = text
        if parent._ws:
            self._create()
    
    def set_text(self, text):
        self._text = text
        if self._parent._ws:
            t = 'document.getElementById("{id}").innerHTML = "{text}"'
            self._parent.eval(t.format(id=self._id, text=text))
    
    def _create(self):
        self._parent.eval(self._TEMPLATE.format(id=self._id, text=self._text))
        
        


class Window(object):
    
    __slots__ = ['_title']
    
    def set_title(self, title):
        pass
        # todo: properties or functions?
