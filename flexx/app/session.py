"""
Definition of App class and the app manager.
"""

import time
import weakref

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
        # name -> (ModelClass, properties, pending, connected) - lists contain Sessions
        self._appinfo = {}
        self._session_map = weakref.WeakValueDictionary()
        self._last_check_time = time.time()
    
    def register_app_class(self, cls, name, properties):
        """ Register a Model class as being an application.
        
        After registering a class, it becomes possible to connect to 
        "http://address:port/ClassName".
        
        Parameters:
          cls (Model): The Model class to serv as an app.
          name (str): The name (relative url path) by which this app can be accessed.
          properties (dict): The model's initial properties.
        """
        name = cls.__name__ if name is None else name
        assert isinstance(cls, type) and issubclass(cls, Model)
        assert isinstance(properties, dict)
        assert isinstance(name, str)
        name = name or '__main__'  # empty string maps to __main__
        if not valid_app_name(name):
            raise ValueError('Given app does not have a valid name %r' % name)
        pending, connected = [], []
        if name in self._appinfo:
            old_cls, old_properties, pending, connected = self._appinfo[name]
            properties, new_properties = old_properties, properties
            properties.update(new_properties)
            if cls is not self._appinfo[name][0]:
                logger.warn('Re-registering app class %r' % name)
        self._appinfo[name] = cls, properties, pending, connected
    
    def create_default_session(self):
        """ Create a default session for interactive use (e.g. the notebook).
        """
        
        if '__default__' in self._appinfo:
            raise RuntimeError('The default session can only be created once.')
        
        session = Session('__default__')
        self._session_map[session.id] = session
        self._appinfo['__default__'] = (None, {}, [session], [])
        return session
    
    def get_default_session(self):
        """ Get the default session that is used for interactive use.
        Returns None unless create_default_session() was called.
        
        When a Model class is created without a session, this method
        is called to get one (and will then fail if it's None).
        """
        x = self._appinfo.get('__default__', None)
        if x is None:
            return None
        else:
            _, _, pending, connected = x
            sessions = pending + connected
            return sessions[-1]
    
    def _clear_old_pending_sessions(self):
        try:
            
            count = 0
            for name in self._appinfo:
                if name == '__default__':
                    continue
                _, _, pending, _ = self._appinfo[name]
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
        elif name not in self._appinfo:
            raise ValueError('Can only instantiate a session with a valid app name.')
        
        cls, properties, pending, connected = self._appinfo[name]
        
        # Session and app class need each-other, thus the _set_app()
        session = Session(name)
        self._session_map[session.id] = session
        app = cls(session=session, is_app=True, **properties)  # is_app marks it as main
        session._set_app(app)
        
        # Now wait for the client to connect. The client will be served
        # a page that contains the session_id. Upon connecting, the id
        # will be communicated, so it connects to the correct session.
        pending.append(session)
        
        logger.debug('Instantiate app client %s' % session.app_name)
        return session
    
    def connect_client(self, ws, name, session_id):
        """ Connect a client to a session that was previously created.
        """
        _, _, pending, connected = self._appinfo[name]
        
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
        _, _, pending, connected = self._appinfo[session.app_name]
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
        _, _, pending, connected = self._appinfo[name]
        return list(connected)
    
    @event.emitter
    def connections_changed(self, name):
        """ Emits an event with the name of the app for which a
        connection is added or removed.
        """
        return {name: str(name)}


# Create global app manager object
manager = AppManager()


# todo: can this like create a window.define() but only if it does not already exist?
# -> if so, this drops the flexx object, and this can be part of PyScript perhaps
# todo: put this in own asset "flexx-require.js"
# todo: we could do something like wait with loading if deps
# are not yet loaded but error when page is already loaded.
# That way we (and our users) wont have to care about import order
MOD_BLA = """
if (typeof window === 'undefined' && typeof module == 'object') {
    global.window = global; // https://github.com/nodejs/node/pull/1838
    window.is_node = true;
}
window._flexx_modules = {};
window.define = function (name, deps, factory) {
    /* Very simple variant of UMD loader */
    if (typeof define === 'function' && define.amd) {
        return define(name, deps, factory);
    }
    dep_vals = [];
    for (var i=0; i<deps.length; i++) {
        if (_flexx_modules[deps[i]] === undefined) {
            throw Error('Unknown dependency: ' + deps[i]);
        }
        dep_vals.push(_flexx_modules[deps[i]]);
    }
    _flexx_modules[name] = factory.apply(null, dep_vals);
};
window.require = function(name) {
    return _flexx_modules[name];
}
"""
       

class Session(SessionAssets):
    """ A session between Python and the client runtime

    This class is what holds together the app widget, the web runtime,
    and the websocket instance that connects to it.
    """
    
    STATUS = new_type('Enum', (), {'PENDING': 1, 'CONNECTED': 2, 'CLOSED': 0})
    
    def __init__(self, app_name):
        super().__init__()
        
        self._app_name = app_name  # name of the app, available before the app itself
        self._runtime = None  # init web runtime, will be set when used
        self._ws = None  # init websocket, will be set when a connection is made
        self._model = None  # Model instance, can be None if app_name is __default__
        self._closing = False
        
        # While the client is not connected, we keep a queue of
        # commands, which are send to the client as soon as it connects
        self._pending_commands = []
        
        # Objects that are guarded from deletion: id: (ping_count, instance)
        self._instances_guarded = {}
        
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
        """ Close the session: close websocket, close runtime, dispose app.
        """
        # Stop guarding objects to break down any circular refs
        for id in list(self._instances_guarded.keys()):
            self._instances_guarded.pop(id)
        self._closing = True  # suppress warnings for session being closed.
        try:
            
            # Close the websocket
            if self._ws:
                self._ws.close_this()
            # Close the runtime
            if self._runtime:
                self._runtime.close()
            # Dispose the model and break the circular reference
            if self._model:
                self._model.dispose()
                self._model = None
        finally:
            self._closing = False
    
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
        if self._closing:
            pass
        elif self.status == self.STATUS.CONNECTED:
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
            logger.error('JS - ' + command[6:].strip() +
                         ' (stack trace in browser console)')
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
    
    def keep_alive(self, ob, iters=4):
        """ Keep an object alive for a certain amount of time, expressed
        in Python-JS ping roundtrips. This is intended for making Model
        objects survive jitter due to synchronisation, though any type
        of object can be given.
        """
        obid = id(ob)
        counter = 0 if self._ws is None else self._ws.ping_counter
        lifetime = counter + int(iters)
        if lifetime > self._instances_guarded.get(obid, (0, ))[0]:
            self._instances_guarded[obid] = lifetime, ob
    
    def _receive_pong(self, count):
        """ Called by ws when it gets a pong. Thus gets called about
        every sec. Clear the guarded Model instances for which the
        "timeout counter" has expired.
        """
        objects_to_clear = [ob for c, ob in
                           self._instances_guarded.values() if c <= count]
        for ob in objects_to_clear:
            self._instances_guarded.pop(id(ob))
    
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
