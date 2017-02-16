"""
Definition of the App class and app manager.
"""

import os
import time
import weakref
from base64 import encodestring as encodebytes

from .. import event, webruntime

from ._model import Model
from ._server import current_server
from ._session import Session, get_page_for_export
from ._assetstore import assets
from . import logger


class ExporterWebSocketDummy:
    """ Object that can be used by an app inplace of the websocket to
    export apps to standalone HTML. The object tracks the commands send
    by the app, so that these can be re-played in the exported document.
    """
    close_code = None
    
    def __init__(self):
        self.commands = []
        self.ping_counter = 0
        # todo: make icon and title work
        #self.command('ICON %s.ico' % session.id)
        # self.command('TITLE %s' % session._runtime_kwargs.get('title', 
        #                                                       'Exported flexx app'))
    
    def command(self, cmd):
        self.commands.append(cmd)


class App:
    """ Specification of a Flexx app.
    
    In the strict sense, this is a container for a Model class plus the
    args and kwargs that it is to be instantiated with.
    
    Arguments:
        cls (Model): the Model class (or Widget) that represents this app.
        args: positional arguments used to instantiate the class (and received
            in its ``init()`` method).
        kwargs: keyword arguments used to initialize the model's properties.
    """
    
    def __init__(self, cls, *args, **kwargs):
        if not isinstance(cls, type) and issubclass(type, Model):
            raise ValueError('App needs a Model class as its first argument.')
        self._cls = cls
        self.args = args
        self.kwargs = kwargs
        self._path = cls.__name__  # can be overloaded by serve()
        self._is_served = False
        
        # Handle good defaults
        if hasattr(cls, 'title') and self.kwargs.get('title', None) is None:
            self.kwargs['title'] = 'Flexx app - ' + cls.__name__
        if hasattr(cls, 'icon') and self.kwargs.get('icon', None) is None:
            # Set icon as base64 str; exported apps can still be standalone
            fname = os.path.abspath(os.path.join(__file__, '..', '..',
                                                    'resources', 'flexx.ico'))
            icon_str = encodebytes(open(fname, 'rb').read()).decode()
            self.kwargs['icon'] = 'data:image/ico;base64,' + icon_str
    
    def __call__(self, *args, **kwargs):
        a = list(self.args) + list(args)
        kw = {}
        kw.update(self.kwargs)
        kw.update(kwargs)
        return self.cls(*a, **kw)
    
    def __repr__(self):
        t = '<App based on class %s pre-initialized with %i args and %i kwargs>'
        return t % (self.cls.__name__, len(self.args), len(self.kwargs))
    
    @property
    def cls(self):
        """ The Model class that is the basis of this app.
        """
        return self._cls
    
    @property
    def is_served(self):
        """ Whether this app is already registered by the app manager.
        """
        return self._is_served
    
    @property
    def url(self):
        """ The url to acces this app. This raises an error if serve() has not
        been called yet or if Flexx' server is not yet running.
        """
        server = current_server(False)
        if not self._is_served:
            raise RuntimeError('Cannot determine app url if app is not yet "served".')
        elif not (server and server.serving):
            raise RuntimeError('Cannot determine app url if the server is not '
                               'yet running.')
        else:
            proto = server.protocol
            host, port = server.serving
            return '%s://%s:%i/%s/' % (proto, host, port, self._path)
    
    @property
    def name(self):
        """ The name of the app, i.e. the url path that this app is served at.
        """
        return self._path or '__main__'
    
    def serve(self, name=None):
        """ Start serving this app.
        
        This registers the given class with the internal app manager. The
        app can be loaded via 'http://hostname:port/app_name'.
        
        Arguments:
            name (str, optional): the relative URL path to serve the app on.
                If this is ``''`` (the empty string), this will be the main app.
        """
        # Note: this talks to the manager; it has nothing to do with the server
        if self._is_served:
            raise RuntimeError('This app (%s) is already served.' % self.name)
        if name is not None:
            self._path = name
        manager.register_app(self)
        self._is_served = True
    
    def launch(self, runtime=None, **runtime_kwargs):
        """ Launch this app as a desktop app in the given runtime.
        
        Arguments:
            runtime (str): the runtime to launch the application in.
                Default 'app or browser'.
            runtime_kwargs: kwargs to pass to the ``webruntime.launch`` function.
                A few names are passed to runtime kwargs if not already present
                ('title' and 'icon').
        
        Returns:
            app (Model): an instance of the given class.
        """
        # Create session
        if not self._is_served:
            self.serve()
        session = manager.create_session(self.name)
        
        # Transfer title and icon
        if runtime_kwargs.get('title', None) is None and 'title' in self.kwargs:
            runtime_kwargs['title'] = self.kwargs['title']
        if runtime_kwargs.get('icon', None) is None and 'icon' in self.kwargs:
            runtime_kwargs['icon'] = self.kwargs['icon']
        
        # Launch web runtime, the server will wait for the connection
        current_server()  # creates server if it did not yet exist
        url = self.url + '?session_id=%s' % session.id
        session._runtime = webruntime.launch(url, runtime=runtime, **runtime_kwargs)
        return session.app
    
    def export(self, filename=None, link=None, write_shared=True):
        """ Export the given Model class to an HTML document.
        
        Arguments:
            filename (str, optional): Path to write the HTML document to.
                If not given or None, will return the html as a string.
            link (int): whether to link assets or embed them:
            
                * 0: all assets are embedded.
                * 1: normal assets are embedded, remote assets remain remote.
                * 2: all assets are linked (as separate files).
                * 3: (default) normal assets are linked, remote assets remain remote.
            write_shared (bool): if True (default) will also write shared assets
                when linking to assets. This can be set to False when
                exporting multiple apps to the same location. The shared assets can
                then be exported last using ``app.assets.export(dirname)``.
        
        Returns:
            html (str): The resulting html. If a filename was specified
            this returns None.
        
        Notes:
            If the given filename ends with .hta, a Windows HTML Application is
            created.
        """
        
        # Prepare name, based on exported file name (instead of cls.__name__)
        if not self._is_served:
            name = os.path.basename(filename).split('.')[0]
            name = name.replace('-', '_').replace(' ', '_')
            self.serve(name)
        
        # Create session with id equal to the app name. This would not be strictly
        # necessary to make exports work, but it makes sure that exporting twice
        # generates the exact same thing (no randomly generated dir names).
        session = manager.create_session(self.name, self.name)
        
        # Make fake connection using exporter object
        exporter = ExporterWebSocketDummy()
        manager.connect_client(exporter, session.app_name, session.id)
        
        # Clean up again - NO keep in memory to ensure two sessions dont get same id
        # manager.disconnect_client(session)
        
        # Warn if this app has data and is meant to be run standalone
        if (not link) and session.get_data_names():
            logger.warn('Exporting a standalone app, but it has registered data.')
        
        # Get HTML - this may be good enough
        html = get_page_for_export(session, exporter.commands, link)
        if filename is None:
            return html
        elif filename.lower().endswith('.hta'):
            hta_tag = '<meta http-equiv="x-ua-compatible" content="ie=edge" />'
            html = html.replace('<head>', '<head>\n    ' + hta_tag, 1)
        elif not filename.lower().endswith(('.html', 'htm')):
            raise ValueError('Invalid extension for exporting to %r' %
                            os.path.basename(filename))
        
        # Save to file. If standalone, all assets will be included in the main html
        # file, if not, we need to export shared assets and session assets too.
        filename = os.path.abspath(os.path.expanduser(filename))
        if link:
            if write_shared:
                assets.export(os.path.dirname(filename))
            session._export_data(os.path.dirname(filename))
        with open(filename, 'wb') as f:
            f.write(html.encode())
        
        app_type = 'standalone app' if link else 'app'
        logger.info('Exported %s to %r' % (app_type, filename))


# todo: thread safety

def valid_app_name(name):
    T = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_0123456789'
    return name and name[0] in T[:-10] and all([c in T for c in name])


class AppManager(event.HasEvents):
    """ Manage apps, or more specifically, the session objects.
    
    There is one AppManager class (in ``flexx.model.manager``). It's
    purpose is to manage the application classes and instances. Intended
    for internal use.
    """
    
    total_sessions = 0  # Keep track how many sessesions we've served in total
    
    def __init__(self):
        super().__init__()
        # name -> (app, pending, connected) - lists contain Session objects
        self._appinfo = {}
        self._session_map = weakref.WeakValueDictionary()
        self._last_check_time = time.time()
    
    def register_app(self, app):
        """ Register an app (an object that wraps a model class plus init args).
        After registering an app (and starting the server) it is
        possible to connect to "http://address:port/app_name".
        """
        assert isinstance(app, App)
        name = app.name
        if not valid_app_name(name):
            raise ValueError('Given app does not have a valid name %r' % name)
        pending, connected = [], []
        if name in self._appinfo:
            old_app, pending, connected = self._appinfo[name]
            if app is not old_app:
                logger.warn('Re-registering app class %r' % name)
        self._appinfo[name] = app, pending, connected
    
    def create_default_session(self, cls=None):
        """ Create a default session for interactive use (e.g. the notebook).
        """
        
        if '__default__' in self._appinfo:
            raise RuntimeError('The default session can only be created once.')
        
        if cls is None:
            cls = Model
        if not isinstance(cls, type) and issubclass(cls, Model):
            raise TypeError('create_default_session() needs a Model subclass.')
        
        # Create app and register it by __default__ name
        app = App(cls)
        app.serve('__default__')  # calls register_app()
        
        # Create the session instance and register it
        session = Session('__default__')
        self._session_map[session.id] = session
        _, pending, connected = self._appinfo['__default__']
        pending.append(session)
        
        # Instantiate the model
        model_instance = app(session=session, is_app=True)
        session._set_app(model_instance)
        
        return session
    
    def get_default_session(self):
        """ Get the default session that is used for interactive use.
        Returns None unless create_default_session() was called earlier.
        
        When a Model class is created without a session, this method
        is called to get one (and will then fail if it's None).
        """
        x = self._appinfo.get('__default__', None)
        if x is None:
            return None
        else:
            _, pending, connected = x
            sessions = pending + connected
            if sessions:
                return sessions[-1]
    
    def _clear_old_pending_sessions(self):
        try:
            
            count = 0
            for name in self._appinfo:
                if name == '__default__':
                    continue
                _, pending, _ = self._appinfo[name]
                to_remove = [s for s in pending
                             if (time.time() - s._creation_time) > 30]
                for s in to_remove:
                    self._session_map.pop(s.id, None)
                    pending.remove(s)
                count += len(to_remove)
            if count:
                logger.warn('Cleared %i old pending sessions' % count)
        
        except Exception as err:
            logger.error('Error when clearing old pending sessions: %s' % str(err))
    
    def create_session(self, name, id=None):
        """ Create a session for the app with the given name.
        
        Instantiate an app and matching session object corresponding
        to the given name, and return the session. The client should
        be connected later via connect_client().
        """
        # Called by the server when a client connects, and from the
        # launch and export functions.
        
        if time.time() - self._last_check_time > 5:
            self._last_check_time = time.time()
            self._clear_old_pending_sessions()
        
        if name == '__default__':
            raise RuntimeError('There can be only one __default__ session.')
        elif name not in self._appinfo:
            raise ValueError('Can only instantiate a session with a valid app name.')
        
        app, pending, connected = self._appinfo[name]
        
        # Create the session
        session = Session(name)
        if id is not None:
            session._id = id  # used by app.export
        self._session_map[session.id] = session
        # Instantiate the model
        # This represents the "instance" of the App object (Model class + args)
        model_instance = app(session=session, is_app=True)
        # Session and app model need each-other, thus the _set_app()
        session._set_app(model_instance)
        
        # Now wait for the client to connect. The client will be served
        # a page that contains the session_id. Upon connecting, the id
        # will be communicated, so it connects to the correct session.
        pending.append(session)
        
        logger.debug('Instantiate app client %s' % session.app_name)
        return session
    
    def connect_client(self, ws, name, session_id):
        """ Connect a client to a session that was previously created.
        """
        _, pending, connected = self._appinfo[name]
        
        # Search for the session with the specific id
        for session in pending:
            if session.id == session_id:
                pending.remove(session)
                break
        else:
            raise RuntimeError('Asked for session id %r, but could not find it' %
                               session_id)
    
        # Add app to connected, set ws
        assert session.status == Session.STATUS.PENDING
        logger.info('New session %s %s' %(name, session_id))
        session._set_ws(ws)
        connected.append(session)
        AppManager.total_sessions += 1
        self.connections_changed(session.app_name)
        return session  # For the ws
    
    def disconnect_client(self, session):
        """ Close a connection to a client.
        
        This is called by the websocket when the connection is closed.
        The manager will remove the session from the list of connected
        instances.
        """
        if session.app_name == '__default__':
            logger.info('Default session lost connection to client.')
            return  # The default session awaits a re-connect
        
        _, pending, connected = self._appinfo[session.app_name]
        try:
            connected.remove(session)
        except ValueError:
            pass
        logger.info('Session closed %s %s' %(session.app_name, session.id))
        session.close()
        self.connections_changed(session.app_name)
    
    def has_app_name(self, name):
        """ Returns the case-corrected name if the given name matches
        a registered appliciation (case insensitive). Returns None if the
        given name does not match any applications.
        """
        name = name.lower()
        for key in self._appinfo.keys():
            if key.lower() == name:
                return key
        else:
            return None
    
    def get_app_names(self):
        """ Get a list of registered application names.
        """
        return [name for name in sorted(self._appinfo.keys())]
    
    def get_session_by_id(self, id):
        """ Get session object by its id
        """
        return self._session_map.get(id, None)
    
    def get_connections(self, name):
        """ Given an app name, return the session connected objects.
        """
        _, pending, connected = self._appinfo[name]
        return list(connected)
    
    @event.emitter
    def connections_changed(self, name):
        """ Emits an event with the name of the app for which a
        connection is added or removed.
        """
        return {name: str(name)}


# Create global app manager object
manager = AppManager()
