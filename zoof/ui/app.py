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

import os
import time
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
    
    def _add_pending_app_instance(self, app):
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
    
    def connect_an_app(self, ws, name, app_id=None):
        """ Connect a pending app instance
        
        Called by the websocket object upon connecting, thus initiating
        the application.
        """
        cls, pending, connected = self._apps[name]
        # Get a pending app instance with specific id, or a new instance
        print('connecting', name, app_id)
        if app_id:
            for app in pending:
                if app.id == app_id:
                    pending.remove(app)
                    break
            else:
                raise RuntimeError('Asked for app id %r, '
                                   'but could not find it' % app_id)
        else:
            app = cls(runtime=None)  # don't create a runtime for it
        # Add app to connected, set ws
        assert app.status == app.STATUS.PENDING
        connected.append(app)
        app._ws = ws  # This is what changes the status to CONNECTED
        # The app can now be used
        ws.command('ICON %s.ico' % app.id)
        ws.command('TITLE %s' % app._config.title)
        app.init()
        return app
    
    def close_an_app(self, app):
        """ Close an application object. This is called by the websocket
        when the connection is closed. The manager will remove the app
        from the list of connected instances.
        """
        cls, pending, connected = self._apps[app.name]
        try:
            connected.remove(app)
        except ValueError:
            pass
    
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


def init_server(host='localhost', port=None):
    global _tornado_app 
    
    # Check that its not already running
    if _tornado_app is not None:
        return
        #raise RuntimeError('zoof.ui server already created')
    
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
    _tornado_app.serving_at = host, port
    print('Serving apps at http://%s:%i/' % (host, port))


def run():  # (runtime='xul', host='localhost', port=None):
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
    
    # Detect App classes in caller namespace
    app_names = manager.get_app_names()
    frame = inspect.currentframe()
    for ob in frame.f_back.f_locals.values():
        if isinstance(ob, type) and issubclass(ob, App):
            #_app_classes.append(ob)
            if ob.__name__ not in app_names:
                manager.register_app_class(ob)
                print('found', ob.__name__)
    
    init_server()
    
    # Start event loop
    _tornado_loop.start()


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

# todo: move to ..util
def create_enum(*members):
    """ Create an enum type from given string arguments.
    """
    assert all([isinstance(m, str) for m in members])
    enums = dict([(s, s) for s in members])
    return type('Enum', (), enums)


# class BaseWidget(object):
#     
#     def __init__(self, parent):
#         self._parent = None
#         self._children = []
#         self._set_parent(parent)
#     
#     @property
#     def parent(self):
#         return self._parent
#     
#     def _set_parent(self, new_parent):
#         old_parent = self._parent
#         if old_parent is not None:
#             while self in old_parent._children:
#                 old_parent._children.remove(self)
#         if new_parent is not None:
#             new_parent._children.append(self)
#         self._parent = new_parent
#     
#     @property
#     def children(self):
#         return list(self._children)

# In tk, tk.Tk() creates the main window, further windows should be
# created with tk.TopLevel()
# In wx, a Frame is the toplevel window
# In Fltk a Frame can be toplevel or not


class App(object):
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
    
    def __init__(self, runtime='xul'):
        #BaseWidget.__init__(self, None)
        # Init websocket, will be set when a connection is made
        self._ws = None
        # Init runtime that is connected with this app instance
        self._runtime = None
        
        # Init
        self._widget_counter = 0
        self._children = []
        
        # Register this app instance
        if runtime == '<export>':
            self._ws = Exporter(self)
            self.init()
        elif runtime:
            manager._add_pending_app_instance(self)
            init_server()
            host, port = _tornado_app.serving_at
            # We associate the runtime with this specific app instance by
            # including the app id to the url. In this way, it is pretty
            # much guaranteed that the runtime will connect to *this* app.
            icon = self._config.icon
            icon = icon if icon.image_sizes() else None
            name = self.name + '-' + self.id
            self._runtime = launch('http://%s:%i/%s/' % (host, port, name), 
                                   runtime=runtime, 
                                   size=self.config.size,
                                   icon=icon, title=self.config.title)
            # Now wait until connected, if possible
            timeout = time.time() + 5.0
            try:
                while (self._ws is None) and (time.time() < timeout):
                    _tornado_loop.run_sync(lambda x=None: None)
                    time.sleep(0.005)
            except RuntimeError:
                print('Tornado event loop already running: Return from app '
                      'initialziation before runtime could connect.')
        
        print('Instantiate app %s' % self.__class__.__name__)
        global default_app
        default_app = self
    
    def __enter__(self):
        from .widget import _default_parent
        _default_parent.append(self)
        return self
    
    def __exit__(self, type, value, traceback):
        from .widget import _default_parent
        assert self is _default_parent.pop(-1)
    
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
    def children(self):
        return list(self._children)
        
    # @property
    # def parent(self):
    #     """ For compatibility with widgets. The parent of an App is
    #     always None.
    #     """
    #     return None
    
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

class Exporter(object):
    """ Export apps to standalone HTML.
    """
    
    def __init__(self, app):
        self._commands = []
        self.close_code = None  # simulate web socket
        
        # todo: how to export icons
        self.command('ICON %s.ico' % app.id)
        self.command('TITLE %s' % app._config.title)
        
    def command(self, cmd):
        self._commands.append(cmd)
    
    def write_html(self, filename):
        html = self.to_html()
        open(filename, 'wt').write(html)
        print('Exported app to %r' % filename)
    
    def to_html(self):
        """ Return HTML string
        """
        from .serve import HTML_DIR
        HTML_BASE = open(os.path.join(HTML_DIR, 'index.html'), 'rt').read()
        
        # Create lines to launch app
        lines = []
        lines.append('zoof.isExported = true;')
        lines.append('')
        lines.append('zoof.runExportedApp = function () {')
        lines.extend(['    zoof.command(%r);' % c for c in self._commands])
        lines.append('};')
        
        # Fill in template
        html = HTML_BASE.replace('zoof.isExported = false;', '\n        '.join(lines))
        
        # Minify
        # todo: these names must be parsed from html or read from serve.py
        for fname in ['serialize.js', 'main.js', 'layouts.js']:
            code = open(os.path.join(HTML_DIR, fname), 'rt').read()
            minified = self._minify(code)
            needle = '<script src="%s"></script>' % fname
            html = html.replace(needle, '<script>%s</script>' % minified)
        for fname in ['main.css']:
            code = open(os.path.join(HTML_DIR, fname), 'rt').read()
            minified = self._minify(code)
            needle = '<link rel="stylesheet" type="text/css" href="%s">' % fname
            html = html.replace(needle, '<style>%s</style>' % minified)
        
        return html
    
    def _minify(self, code):
        """ Very minimal JS minification algorithm. Can probably be better.
        May contain bugs. Only operates well on JS without syntax errors.
        """
        space_safe = ' =+-/*&|(){},.><:;'
        chars = ['\n']
        self._i = -1
        def read():
            self._i += 1
            if self._i < len(code):
                return code[self._i]
        def to_end_of_string(c0):
            chars.append(c0)
            while True:
                c = read()
                chars.append(c)
                if c == c0 and chars[-1] != '\\':
                    return
        def to_end_of_line_comment():
            while True:
                c = read()
                if c == '\n':
                    return
        def to_end_of_mutiline_comment():
            lastchar = ''
            while True:
                c = read()
                if c == '/' and lastchar == '*':
                    return
                lastchar = c
        while True:
            c = read()
            if not c:
                break  # end of code
            elif c == "'" or c == '"':
                to_end_of_string(c)
            elif c == '/' and chars[-1] == '/':
                chars.pop(-1)
                to_end_of_line_comment()
            elif c == '*' and chars[-1] == '/':
                chars.pop(-1)
                to_end_of_mutiline_comment()
            elif c in '\t\r\n':
                pass
            elif c in ' ':
                if chars[-1] not in space_safe:
                    chars.append(c)
            elif c in space_safe and chars[-1] == ' ':
                chars[-1] = c  # replace last char
            else:
                chars.append(c)
        chars.pop(0)
        return ''.join(chars)


default_app = None
def current_app():
    global default_app
    if default_app is None:
        default_app = App()
    return default_app

class DefaultApp(App):
    pass

