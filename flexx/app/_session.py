"""
Definition of the Session class.
"""

import time
import json
import random
import hashlib
import weakref

from ._model import Model, new_type
from ._asset import Asset, Bundle, solve_dependencies
from ._assetstore import AssetStore, export_assets_and_data, INDEX
from ._assetstore import assets as assetstore
from . import logger

reprs = json.dumps


# Use the system PRNG for session id generation (if possible)
# NOTE: secure random string generation implementation is adapted
#       from the Django project. 

def get_random_string(length=24, allowed_chars=None):
    """ Produce a securely generated random string.
    
    With a length of 12 with the a-z, A-Z, 0-9 character set returns
    a 71-bit value. log_2((26+26+10)^12) =~ 71 bits
    """
    allowed_chars = allowed_chars or ('abcdefghijklmnopqrstuvwxyz' +
                                      'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
    try:
        srandom = random.SystemRandom()
    except NotImplementedError:  # pragma: no cover
        srandom = random
        logger.warn('Falling back to less secure Mersenne Twister random string.')
        bogus = "%s%s%s" % (random.getstate(), time.time(), 'sdkhfbsdkfbsdbhf')
        random.seed(hashlib.sha256(bogus.encode()).digest())

    return ''.join(srandom.choice(allowed_chars) for i in range(length))


class Session:
    """ A session between Python and the client runtime.
    This class is what holds together the app widget, the web runtime,
    and the websocket instance that connects to it.
    
    Responsibilities:
    
    * Send messages to the client and parse messages received by the client.
    * Keep track of Model instances associated with the session.
    * Ensure that the client has all the module definitions it needs.
    * Allow the user to send data to the client.
    
    """
    
    STATUS = new_type('Enum', (), {'PENDING': 1, 'CONNECTED': 2, 'CLOSED': 0})
    
    def __init__(self, app_name, store=None):  # Allow custom store for testing
        self._store = store if (store is not None) else assetstore
        assert isinstance(self._store, AssetStore)
        
        self._creation_time = time.time()  # used by app manager
        
        # Id and name of the app
        self._id = get_random_string()
        self._app_name = app_name
        
        # To keep track of what modules are defined at the client
        self._present_classes = set()  # Model classes known by the client
        self._present_modules = set()  # module names that, plus deps
        self._present_assets = set()  # names of used associated assets
        self._assets_to_ignore = set()  # user settable
        
        # Data for this session (in addition to the data provided by the store)
        self._data = {}
        self._data_volatile = {}  # deleted after retrieving
        
        # More vars
        self._runtime = None  # init web runtime, will be set when used
        self._ws = None  # init websocket, will be set when a connection is made
        self._model = None  # Model instance, can be None if app_name is __default__
        self._closing = False  # Flag to help with shutdown
        
        # The session assigns model id's, keeps track of model objects and
        # sometimes keeps them alive for a short while.
        self._model_counter = 0
        self._model_instances = weakref.WeakValueDictionary()
        self._instances_guarded = {}  # id: (ping_count, instance)
        
        # While the client is not connected, we keep a queue of
        # commands, which are send to the client as soon as it connects
        self._pending_commands = []
    
    def __repr__(self):
        t = '<%s for %r (%i) at 0x%x>'
        return t % (self.__class__.__name__, self.app_name, self.status, id(self))
    
    @property
    def id(self):
        """ The unique identifier of this session.
        """
        return self._id
    
    @property
    def app_name(self):
        """ The name of the application that this session represents.
        """
        return self._app_name
    
    @property
    def app(self):
        """ The Model instance that represents the app.
        """
        return self._model
    
    @property
    def runtime(self):
        """ The runtime that is rendering this app instance. Can be
        None if the client is a browser.
        """
        return self._runtime
    
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
    
    @property
    def present_modules(self):
        """ The set of module names that is (currently) available at the client.
        """
        return set(self._present_modules)
    
    @property
    def assets_to_ignore(self):
        """ The set of names of assets that should *not* be pushed to
        the client, e.g. because they are already present on the page.
        Add names to this set to prevent them from being loaded.
        """
        return self._assets_to_ignore
    
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
            # Discard data
            self._data = {}
            self._data_volatile = {}
        finally:
            self._closing = False
    
    ## Hooking up with app, websocket, runtime
    
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
        self._ws.command('INIT-DONE')
   
    def _set_app(self, model):
        if self._model is not None:
            raise RuntimeError('Session already has an associated Model.')
        self._model = model
    
    def _set_runtime(self, runtime):
        if self._runtime is not None:
            raise RuntimeError('Session already has a runtime.')
        self._runtime = runtime
    
    ## Data
    
    def _send_data(self, id, data, meta):
        """ Send data to a model on the JS side. The corresponding object's
        receive_data() method is called when the data is available in JS.
        This is called by ``Model.send_data()`` and works in the same way.
        """
        # Check id
        if not isinstance(id, str):
            raise TypeError('session.send_data() first arg must be a str id.')
        if not self._model_instances.get(id, None):
            raise ValueError('session.send_data() first arg must be an id '
                             'corresponding to an existing model: %r' % id)
        # Check meta
        if not isinstance(meta, dict):
            raise TypeError('session.send_data() meta must be a dict.')
        # Check data - url or blob
        data_name = None
        if isinstance(data, str):
            # Perhaps a URL: tell client to retrieve it with AJAX
            if data.startswith(('https://', 'http://', '/flexx/data/')):
                url = data
            elif data.startswith('_data/'):
                url = '/flexx/' + data[1:]  # prevent one redirect
            else:
                raise TypeError('session.send_data() got a string, but does '
                                'not look like a URL: %r' % data)
        elif isinstance(data, bytes):
            # Blob: store it, and tell client to retieve it with AJAX
            # todo: have a second ws connection for pushing data
            data_name = 'blob-' + get_random_string()
            url = '/flexx/data/%s/%s' % (self.id, data_name)
            self._data_volatile[data_name] = data
            if self.id == self.app_name:  # Maintain data if we're being exported
                self._data[data_name] = data
        else:
            raise TypeError('session.send_data() data must be a bytes or a URL, '
                            'not %s.' % data.__class__.__name__)
        
        # Tell JS to retrieve data
        t = 'window.flexx.instances.%s.retrieve_data("%s", %s);'
        self._exec(t % (id, url, reprs(meta)))
    
    def add_data(self, name, data):
        """ Add data to serve to the client (e.g. images), specific to this
        session. Returns the link at which the data can be retrieved.
        See ``Session.send_data()`` for a send-and-forget mechanism, and
        ``app.assets.add_shared_data()`` to provide shared data.
        
        Parameters:
            name (str): the name of the data, e.g. 'icon.png'. If data has
                already been set on this name, it is overwritten.
            data (bytes): the data blob.
        
        Returns:
            url: the (relative) url at which the data can be retrieved.
        """
        if not isinstance(name, str):
            raise TypeError('Session.add_data() name must be a str.')
        if name in self._data:
            raise ValueError('Session.add_data() got existing name %r.' % name)
        if not isinstance(data, bytes):
            raise TypeError('Session.add_data() data must be bytes.')
        self._data[name] = data
        return '_data/%s/%s' % (self.id, name)  # relative path so it works /w export
    
    def remove_data(self, name):
        """ Remove the data associated with the given name. If you need this,
        also consider ``send_data()``. Also note that data is automatically
        released when the session is closed.
        """
        self._data.pop(name, None)
    
    def get_data_names(self):
        """ Get a list of names of the data provided by this session.
        """
        return list(self._data.keys())
    
    def get_data(self, name):
        """ Get the data corresponding to the given name. This can be
        data local to the session, or global data. Returns None if data
        by that name is unknown.
        """
        if True:
            data = self._data_volatile.pop(name, None)
        if data is None:
            data = self._data.get(name, None)
        if data is None:
            data = self._store.get_data(name)
        return data
    
    def _export_data(self, dirname, clear=False):
        """ Export all assets and data specific to this session.
        Private method, used by app.export().
        """
        # Note that self.id will have been set to the app name.
        assets = []
        data = [(name, self.get_data(name)) for name in self.get_data_names()]
        export_assets_and_data(assets, data, dirname, self.id, clear)
        logger.info('Exported data for %r to %r.' % (self.id, dirname))

    ## Keeping track of model objects
    
    def _register_model(self, model):
        """ Called by Model to give them an id and register with the session.
        """
        assert isinstance(model, Model)
        assert model.session is self
        cls = model.__class__
        # Set id
        self._model_counter += 1
        model._id = cls.__name__ + str(self._model_counter)
        # Register the instance using a weakref
        self._model_instances[model.id] = model
        # Register the class to that the client has the needed definitions
        self._register_model_class(cls)
    
    def get_model_instance_by_id(self, id):
        """ Get instance of Model class corresponding to the given id,
        or None if it does not exist.
        """
        try:
            return self._model_instances[id]
        except KeyError:
            t = 'Model instance %r does not exist in this session (anymore).'
            logger.warn(t % id)
            return None  # Could we revive it? ... probably not a good idea
    
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
    
    ## JIT asset definitions
    
    # todo: deprecated - remove this
    def register_model_class(self, cls):
        logger.warn('register_model_class() is no more.')
    
    def _register_model_class(self, cls):
        """ Mark the given Model class as used; ensure that the client
        knows about the module that it is defined in, dependencies
        of this module, and associated assets of any of these modules.
        """
        if not (isinstance(cls, type) and issubclass(cls, Model)):
            raise TypeError('_register_model_class() needs a Model class')
        # Early exit if we know the class already
        if cls in self._present_classes:
            return
        
        # Make sure that no two models have the same name, or we get problems
        # that are difficult to debug. Unless classes are defined interactively.
        # The modules of classes that are re-registered are re-defined. The base
        # class of such a model is assumed to be either unchanged or defined
        # in the same module. It can also happen that a class is registered for
        # which the module was defined earlier (e.g. ui.html). Such modules
        # are redefined as well.
        same_name = [c for c in self._present_classes if c.__name__ == cls.__name__]
        if same_name:
            is_interactive = self._app_name == '__default__'
            same_name.append(cls)
            is_dynamic_cls = all([c.__module__ == '__main__' for c in same_name])
            if not (is_interactive and is_dynamic_cls):
                raise RuntimeError('Cannot have multiple Model classes with the same '
                                   'name unless using interactive session and the '
                                   'classes are dynamically defined: %r' % same_name)
        
        # Mark the class and the module as used
        logger.debug('Registering Model class %r' % cls.__name__)
        self._register_module(cls.__jsmodule__, True)
    
    def _register_module(self, mod_name, force=False):
        """ Register a module with the client, as well as its
        dependencies, and associated assests of the module and its
        dependencies. If the module was already defined, it is
        re-defined.
        """
        
        modules = set()
        assets = []
        
        def collect_module_and_deps(mod):
            if mod.name.startswith('flexx.app'):
                return  # these are part of flexx-core asset
            if mod.name not in self._present_modules: 
                self._present_modules.add(mod.name)
                for dep in mod.deps:
                    submod = self._store.modules[dep]
                    collect_module_and_deps(submod)
                modules.add(mod)
        
        # Collect module and dependent modules that are not yet defined
        self._store.update_modules()  # Ensure up-to-date module definition
        mod = self._store.modules[mod_name]
        collect_module_and_deps(mod)
        f = lambda m: (m.name.startswith('__main__'), m.name)
        modules = solve_dependencies(sorted(modules, key=f))
        
        # Collect associated assets
        for mod in modules:
            for asset_name in self._store.get_associated_assets(mod.name):
                if asset_name not in self._present_assets:
                    self._present_assets.add(asset_name)
                    assets.append(self._store.get_asset(asset_name))
        # If the module was already defined and thus needs to be re-defined,
        # we only redefine *this* module, no deps and no assoctated assets.
        if not modules:
            modules.append(mod)
        # Collect CSS and JS assets
        for mod in modules:
            if mod.get_css().strip():
                assets.append(self._store.get_asset(mod.name + '.css'))
        for mod in modules:
            assets.append(self._store.get_asset(mod.name + '.js'))
        
        # Mark classes as used
        for mod in modules:
            for cls in mod.model_classes:
                self._present_classes.add(cls)
        
        # Push assets over the websocket. Note how this works fine with the
        # notebook because we turn ws commands into display(HTML()).
        # JS can be defined via eval() or by adding a <script> to the DOM.
        # The latter allows assets that do not use strict mode, but sourceURL
        # does not work on FF. So we only want to eval our own assets.
        for asset in assets:
            if asset.name in self._assets_to_ignore:
                continue
            logger.debug('Loading asset %s' % asset.name)
            # Determine command suffix. All our sources come in bundles,
            # for which we use eval because it makes sourceURL work on FF.
            suffix = asset.name.split('.')[-1].upper()
            if suffix == 'JS' and isinstance(asset, Bundle):
                suffix = 'JS-EVAL'
            t = 'DEFINE-%s %s %s'
            self._send_command(t % (suffix, asset.name, asset.to_string()))
    
    ## Communication with the client
    
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
            _, id, name, txt = command.split(' ', 3)
            ob = self._model_instances.get(id, None)
            if ob is not None:
                ob._set_prop_from_js(name, txt)
        elif command.startswith('SET_EVENT_TYPES '):
            _, id, txt = command.split(' ', 3)
            ob = self._model_instances.get(id, None)
            if ob is not None:
                ob._set_event_types_js(txt)
        elif command.startswith('EVENT '):
            _, id, name, txt = command.split(' ', 3)
            ob = self._model_instances.get(id, None)
            if ob is not None:
                ob._emit_from_js(name, txt)
        else:
            logger.warn('Unknown command received from JS:\n%s' % command)
    
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


## Functions to get page
# These could be methods, but theses are only for internal use

def get_page(session):
    """ Get the string for the HTML page to render this session's app.
    """
    css_assets = [assetstore.get_asset('reset.css')]
    js_assets = [assetstore.get_asset('flexx-core.js')]
    return _get_page(session, js_assets, css_assets, 3, False)


def get_page_for_export(session, commands, link=0):
    """ Get the string for an exported HTML page (to run without a server).
    """
    # We start as a normal page ...
    css_assets = [assetstore.get_asset('reset.css')]
    js_assets = [assetstore.get_asset('flexx-core.js')]
    # Get all the used modules
    modules = [assetstore.modules[name] for name in session.present_modules]
    f = lambda m: (m.name.startswith('__main__'), m.name)
    modules = solve_dependencies(sorted(modules, key=f))
    # First the associated assets
    asset_names = set()
    for mod in modules:
        for asset_name in assetstore.get_associated_assets(mod.name):
            if asset_name not in asset_names:
                asset_names.add(asset_name)
                asset = assetstore.get_asset(asset_name)
                if asset.name.lower().endswith('.js'):
                    js_assets.append(asset)
                else:
                    css_assets.append(asset)
    # Then the modules themselves
    for mod in modules:
        if mod.get_css().strip():
            css_assets.append(assetstore.get_asset(mod.name + '.css'))
    for mod in modules:
        js_assets.append(assetstore.get_asset(mod.name + '.js'))
    # Create asset for launching the app (commands that normally get send
    # over the websocket)
    lines = []
    lines.append('flexx.is_exported = true;\n')
    lines.append('flexx.runExportedApp = function () {')
    lines.extend(['    flexx.command(%s);' % reprs(c) for c in commands
                  if not c.startswith('DEFINE-')])
    lines.append('};\n')
    # Create a session asset for it, "-export.js" is always embedded
    export_asset = Asset('flexx-export.js', '\n'.join(lines))
    js_assets.append(export_asset)
    
    return _get_page(session, js_assets, css_assets, link, True)


def _get_page(session, js_assets, css_assets, link, export):
    """ Compose index page.
    """
    pre_path = '_assets' if export else '/flexx/assets'
    
    codes = []
    
    t = 'var flexx = {app_name: "%s", session_id: "%s"};'
    codes.append('<script>%s</script>\n' % t % (session.app_name, session.id))
    
    for assets in [css_assets, js_assets]:
        for asset in assets:
            if not link:
                html = asset.to_html('{}', link)
            else:
                if asset.name.endswith(('-info.js', '-export.js')):
                    html = asset.to_html('', 0)
                else:
                    html = asset.to_html(pre_path + '/shared/{}', link)
            codes.append(html)
            if export and assets is js_assets:
                codes.append('<script>window.flexx.spin();</script>')
        codes.append('')  # whitespace between css and js assets
    
    src = INDEX
    if not link:
        asset_names = [a.name for a in css_assets + js_assets]
        toc = '<!-- Contents:\n\n- ' + '\n- '.join(asset_names) + '\n\n-->'
        codes.insert(0, toc)
        src = src.replace('ASSET-HOOK', '\n\n\n'.join(codes))
    else:
        src = src.replace('ASSET-HOOK', '\n'.join(codes))
    
    return src
