"""
Definition of App class and the app manager.
"""

import time

from .. import event
from .model import Model, new_type
from .assetstore import SessionAssets
from . import logger

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
        # name -> (ModelClass, pending, connected) - lists contain proxies
        self._proxies = {}
        self._last_check_time = time.time()
    
    def register_app_class(self, cls):
        """ Register a Model class as being an application.
        
        Applications are identified by the ``__name__`` attribute of
        the class. The given class must inherit from ``Model``.
        
        After registering a class, it becomes possible to connect to 
        "http://address:port/ClassName". 
        """
        assert isinstance(cls, type) and issubclass(cls, Model)
        name = cls.__name__
        if not valid_app_name(name):
            raise ValueError('Given app does not have a valid name %r' % name)
        pending, connected = [], []
        if name in self._proxies and cls is not self._proxies[name][0]:
            oldCls, pending, connected = self._proxies[name]
            logger.warn('Re-registering app class %r' % name)
            #raise ValueError('App with name %r already registered' % name)
        self._proxies[name] = cls, pending, connected
    
    def create_default_session(self):
        """ Create a default session for interactive use (e.g. the notebook).
        """
        
        if '__default__' in self._proxies:
            raise RuntimeError('The default session can only be created once.')
        
        session = Session('__default__')
        self._proxies['__default__'] = (None, [session], [])
        return session
    
    def get_default_session(self):
        """ Get the default session that is used for interactive use.
        Returns None unless create_default_session() was called.
        
        When a Model class is created without a session, this method
        is called to get one (and will then fail if it's None).
        """
        x = self._proxies.get('__default__', None)
        if x is None:
            return None
        else:
            _, pending, connected = x
            proxies = pending + connected
            return proxies[-1]
    
    def _clear_old_pending_sessions(self):
        try:
            
            count = 0
            for name in self._proxies:
                if name == '__default__':
                    continue
                _, pending, _ = self._proxies[name]
                to_remove = [s for s in pending
                             if (time.time() - s._creation_time) > 10]
                for s in to_remove:
                    pending.remove(s)
                count += len(to_remove)
            if count:
                logger.warn('Cleared %i old pending sessions' % count)
        
        except Exception as err:
            logger.error('Error when clearing old pending sessions: %s' % str(err))
    
    def create_session(self, name):
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
        elif name not in self._proxies:
            raise ValueError('Can only instantiate a session with a valid app name.')
        
        cls, pending, connected = self._proxies[name]
        
        # Session and app class need each-other, thus the _set_app()
        session = Session(cls.__name__)
        app = cls(session=session, is_app=True)  # is_app marks this Model as "main"
        session._set_app(app)
        
        # Now wait for the client to connect. The client will be served
        # a page that contains the session_id. Upon connecting, the id
        # will be communicated, so it connects to the correct session.
        pending.append(session)
        
        logger.debug('Instantiate app client %s' % session.app_name)
        return session
    
    def connect_client(self, ws, name, app_id):
        """ Connect a client to a session that was previously created.
        """
        cls, pending, connected = self._proxies[name]
        
        # Search for the session with the specific id
        for session in pending:
            if session.id == app_id:
                pending.remove(session)
                break
        else:
            raise RuntimeError('Asked for app id %r, but could not find it' % app_id)
    
        # Add app to connected, set ws
        assert session.status == Session.STATUS.PENDING
        logger.info('New session %s %s' %(name, app_id))
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
        cls, pending, connected = self._proxies[session.app_name]
        try:
            connected.remove(session)
        except ValueError:
            pass
        logger.info('Session closed %s %s' %(session.app_name, session.id))
        session.close()
        self.connections_changed(session.app_name)
    
    def has_app_name(self, name):
        """ Returns True if name is a registered appliciation name
        """
        return name in self._proxies.keys()
    
    def get_app_names(self):
        """ Get a list of registered application names (excluding those
        that start with an underscore).
        """
        return [name for name in self._proxies.keys() if not name.startswith('_')]
    
    def get_session_by_id(self, name, id):
        """ Get session object by name and id
        """
        cls, pending, connected = self._proxies[name]
        for session in pending:
            if session.id == id:
                return session
        for session in connected:
            if session.id == id:
                return session
    
    def get_connections(self, name):
        """ Given an app name, return the session connected objects.
        """
        cls, pending, connected = self._proxies[name]
        return list(connected)
    
    @event.emitter
    def connections_changed(self, name):
        """ Emits an event with the name of the app for which a
        connection is added or removed.
        """
        return {name: str(name)}


# Create global app manager object
manager = AppManager()


class Session(SessionAssets):
    """ A session between Python and the client runtime

    This class is what holds together the app widget, the web runtime,
    and the websocket instance that connects to it.
    """
    
    STATUS = new_type('Enum', (), {'PENDING': 1, 'CONNECTED': 2, 'CLOSED': 0})
    
    def __init__(self, app_name):
        super().__init__()
        
        # Init assets
        id_asset = ('var flexx_session_id = "%s";\n' % self.id).encode()
        self.add_asset('index-flexx-id.js', id_asset)
        self.use_global_asset('pyscript-std.js')
        self.use_global_asset('flexx-app.js')
        
        self._app_name = app_name  # name of the app, available before the app itself
        self._runtime = None  # init web runtime, will be set when used
        self._ws = None  # init websocket, will be set when a connection is made
        self._model = None  # Model instance, can be None if app_name is __default__
        
        # While the client is not connected, we keep a queue of
        # commands, which are send to the client as soon as it connects
        self._pending_commands = []
        
        self._creation_time = time.time()
    
    def __repr__(self):
        s = self.status
        return '<Session for %r (%i) at 0x%x>' % (self.app_name, s, id(self))
    
    @property
    def app_name(self):
        """ The name of the application that this session represents.
        """
        return self._app_name
    
    @property
    def app(self):
        """ The Model instance that represents the app. Can be None if Flexx
        is used in interactive mode (using the ``__default__`` app).
        """
        return self._model
    
    @property
    def runtime(self):
        """ The runtime that is rendering this app instance. Can be
        None if the client is a browser.
        """
        return self._runtime
    
    def _set_ws(self, ws):
        """ A session is always first created, so we know what page to
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
   
    def _set_app(self, model):
        if self._model is not None:
            raise RuntimeError('Session already has an associated Model.')
        self._model = model
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
        if self._model:
            self._model.dispose()
            self._model = None  # break circular reference
    
    @property
    def status(self):
        """ The status of this session. The lifecycle for each session is:
        
        * status 1: pending
        * statys 2: connected
        * status 0: closed
        """
        if self._ws is None:
            return self.STATUS.PENDING  # not connected yet
        elif self._ws.close_code is None:
            return self.STATUS.CONNECTED  # alive and kicking
        else:
            return self.STATUS.CLOSED  # connection closed
    
    def _send_command(self, command):
        """ Send the command, add to pending queue.
        """
        if self.status == self.STATUS.CONNECTED:
            self._ws.command(command)
        elif self.status == self.STATUS.PENDING:
            self._pending_commands.append(command)
        else:
            #raise RuntimeError('Cannot send commands; app is closed')
            logger.warn('Cannot send commands; app is closed')
    
    def _receive_command(self, command):
        """ Received a command from JS.
        """
        if command.startswith('RET '):
            print(command[4:])  # Return value
        elif command.startswith('ERROR '):
            logger.error('JS - ' + command[6:].strip())
        elif command.startswith('WARN '):
            logger.warn('JS - ' + command[5:].strip())
        elif command.startswith('PRINT '):
            print(command[5:].strip())
        elif command.startswith('INFO '):
            logger.info('JS - ' + command[5:].strip())
        elif command.startswith('SET_PROP '):
            # todo: seems weird to deal with here. implement by registring some handler?
            # Should be better when we implement a more formal protocol
            _, id, name, txt = command.split(' ', 3)
            ob = Model._instances.get(id, None)
            if ob is not None:
                ob._set_prop_from_js(name, txt)
        elif command.startswith('SET_EVENT_TYPES '):
            _, id, txt = command.split(' ', 3)
            ob = Model._instances.get(id, None)
            if ob is not None:
                ob._set_event_types_js(txt)
        elif command.startswith('EVENT '):
            _, id, name, txt = command.split(' ', 3)
            ob = Model._instances.get(id, None)
            if ob is not None:
                ob._emit_from_js(name, txt)
        else:
            logger.warn('Unknown command received from JS:\n%s' % command)
    
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
