"""
Definition of App class and the app manager.
"""

import time
import json
import random
import hashlib
from urllib.request import urlopen

from .. import config

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


class SessionAssets:
    """ Provider for assets of a specific session. Inherited by Session.
    
    The responsibility of this class is to keep track of what JSModules
    are being used, to provide the associated bundles and assets, and to
    dynamically define assets when needed. Further this class takes
    care of per-session data.
    """
    
    def __init__(self, store=None):  # Allow custom store for testing
        self._store = store if (store is not None) else assetstore
        assert isinstance(self._store, AssetStore)
        
        self._id = get_random_string()
        self._app_name = ''
        
        # Keep track of all assets for this session. Assets that are provided
        # by the asset store have a value of None.
        self._used_classes = set()  # Model classes registered as used
        self._used_modules = set()  # module names that define used classes, plus deps
        self._loaded_modules = set()  # module names that were present in bundles
        # Data for this session (in addition to the data provided by the store)
        # todo: get rid of session assets alltogether, or is there a use-case?
        self._assets = {}
        self._data = {}
        # Whether the page has been served already
        self._served = 0
        self._is_interactive = None
    
    @property
    def id(self):
        """ The unique identifier of this session.
        """
        return self._id
    
    def get_data_names(self):
        """ Get a list of names of the data provided by this session, in
        the order that they were added.
        """
        return list(self._data.keys())  # Note: order matters
    
    def get_data(self, name):
        """ Get the data corresponding to the given name. This can be
        data local to the session, or global data. Returns None if data
        by that name is unknown.
        """
        data = self._data.get(name, None)
        if data is None:
            data = self._store.get_data(name)
        return data
    
    # todo: the way that we do assets now makes me wonder whether there are better ways
    # to deal with data handling ...
    
    def add_data(self, name, data):  # todo: add option to clear data after its loaded?
        """ Add data to serve to the client (e.g. images), specific to this
        session. Returns the link at which the data can be retrieved.
        See ``app.assets.add_shared_data()`` to provide shared data.
        
        Parameters:
            name (str): the name of the data, e.g. 'icon.png'. If data has
                already been set on this name, it is overwritten.
            data (bytes): the data blob. Can also be a uri to the blob
                (string starting with "file://", "http://" or "https://").
        """
        if not isinstance(name, str):
            raise TypeError('Session.add_data() name must be a str.')
        if name in self._data:
            raise ValueError('Session.add_data() got existing name %r.' % name)
        if isinstance(data, str):
            if data.startswith('file://'):
                data = open(data.split('//', 1)[1], 'rb').read()
            elif data.startswith(('http://', 'https://')):
                data = urlopen(data, timeout=5.0).read()
        if not isinstance(data, bytes):
            raise TypeError('Session.add_data() data must be a bytes.')
        self._data[name] = data
        return '_data/%s/%s' % (self.id, name)  # relative path so it works /w export
    
    def remove_data(self, name):
        """ Remove the data associated with the given name.
        """
        self._data.pop(name, None)
    
    def register_model_class(self, cls):
        """ Mark the given Model class as used; ensure that the client
        knows about it.
        """
        if not (isinstance(cls, type) and issubclass(cls, Model)):
            raise ValueError('Not a Model class')
            
        # Early exit if we know the class already
        if cls in self._used_classes:
            return
        
        # Make sure the base classes are registered first
        for cls2 in cls.mro()[1:]:
            if not issubclass(cls2, Model):  # True if cls2 is *the* Model class
                break
            if cls2 not in self._used_classes:
                self.register_model_class(cls2)
        
        # Ensure interactive flag - e.g. for in the notebook
        if self._is_interactive is None:
            self._is_interactive = self._app_name == '__default__'
        
        # Make sure that no two models have the same name, or we get problems
        # that are difficult to debug. Unless classes are defined in the notebook.
        same_name = [c for c in self._used_classes if c.__name__ == cls.__name__]
        if same_name:
            same_name.append(cls)
            is_dynamic_cls = all([c.__module__ == '__main__' for c in same_name])
            if not (self._is_interactive and is_dynamic_cls):
                raise RuntimeError('Cannot have multiple Model classes with the same '
                                   'name unless using interactive session and the '
                                   'classes are dynamically defined: %r' % same_name)
        
        # Mark the class and the module as used
        logger.debug('Registering Model class %r' % cls.__name__)
        self._used_classes.add(cls)
        self._store.update_modules(cls)  # Update module definition
        self._register_module(cls.__jsmodule__)
    
    def _register_module(self, mod_name):
        """ Mark a module (and its dependencies) as used. If the page is
        already served, will inject the module dynamically.
        """
        
        if not self._served:
            # Not served yet, register asset as used so we can serve it later
            if mod_name not in self._used_modules:
                self._used_modules.add(mod_name)
                mod = self._store.modules[mod_name]
                for dep in mod.deps:
                    self._register_module(dep)
        
        else:
            # Already served, we might need to load dynamically. We simply
            # check whether a module is new or has changed since its source
            # was last obtained. E.g. it could be that its a new class for 
            # this session, but that it was loaded as part of the bundle.
            mod = self._store.modules[mod_name]
            modules = [m for m in self._store.modules.values()
                       if m.name not in self._loaded_modules or
                       m.changed_time >= self._served]
            modules = solve_dependencies(modules)  # sort based on deps
            if modules:
                # Bundles - the dash makes this bundle have an empty "module name"
                js_asset = Bundle('-extra.js')
                css_asset = Bundle('-extra.css')
                for mod in modules:
                    js_asset.add_module(mod)
                    css_asset.add_module(mod)
                # Load assets of modules that were not yet used
                for mod in modules:
                    if mod.name not in self._used_modules:
                        for asset in self._store.get_associated_assets(mod.name):
                            self._inject_asset_dynamically(asset)
                # Load bundles
                self._inject_asset_dynamically(css_asset)
                self._inject_asset_dynamically(js_asset)
                # Mark the modules as used and loaded
                for mod in modules:
                    self._used_modules.add(mod.name)
    
    def _inject_asset_dynamically(self, asset):
        """ Load an asset in a running session.
        This method assumes that this is a Session class.
        """
        logger.debug('Dynamically loading asset %r' % asset.name)
        
        in_notebook = (self._is_interactive and
                       getattr(self, 'init_notebook_done', False))
        
        if in_notebook:
            # Load using IPython constructs
            from IPython.display import display, HTML
            if asset.name.lower().endswith('.js'):
                display(HTML("<script>%s</script>" % asset.to_string()))
            else:
                display(HTML("<style>%s</style>" % asset.to_string()))
        else:
            # Load using Flexx construct (using Session._send_command())
            suffix = asset.name.split('.')[-1].upper()
            self._send_command('DEFINE-%s %s' % (suffix, asset.to_string()))
    
    def get_assets_in_order(self, css_reset=False, load_all=None, bundle_level=None):
        """ Get two lists containing the JS assets and CSS assets,
        respectively. The assets contain bundles corresponding to all modules
        being used (and their dependencies). The order of bundles is based on
        the dependency resolution. The order of other assets is based on the
        order in which assets were instantiated. Special assets are added, such
        as the CSS reset and the JS module loader.
        
        After this function gets called, it is assumed that the assets have
        been served and that future asset loads should be done dynamically.
        """
        
        # Make store aware of everything that we know now
        self._store.update_modules()
        
        if load_all is None:
            load_all = config.bundle_all
        if load_all:
            modules_to_load = self._store.modules.keys()  # e.g. notebook
        else:
            modules_to_load = self._used_modules
        
        # Get bundle names that contain all the used modules. We use
        # bundledversions, which means that we load more modules than
        # we use. In this step we can make a lot of choices with regard
        # to how much modules we want to pack in a bundle. We could use
        # a different depth per branch, we could create session-specific
        # bundles, we could allow users to define a bundle, etc. For
        # now, we just truncate at a certain level.
        # todo: this could be configurable, e.g. 99 for dev, 1 for prod
        level = max(1, bundle_level or 2)
        bundle_names = set()
        for mod_name in modules_to_load:
            bundle_names.add('.'.join(mod_name.split('.')[:level]))
        
        # Get bundles
        js_assets = [self._store.get_asset(b + '.js') for b in bundle_names]
        css_assets = [self._store.get_asset(b + '.css') for b in bundle_names]
        
        # Get loaded modules
        for asset in js_assets:
            self._loaded_modules.update([m.name for m in asset.modules])
        
        # Sort bundles by name and dependency resolution
        f = lambda m: (m.name.startswith('__main__'), m.name)
        js_assets = solve_dependencies(sorted(js_assets, key=f))
        css_assets = solve_dependencies(sorted(css_assets, key=f))
        
        # Filter out empty css bundles
        css_assets = [asset for asset in css_assets
                      if any([m.get_css().strip() for m in asset.modules])]
        
        # Collect non-module assets
        # Assets only get included if they are in a module that is *used*.
        asset_deps_before = set()
        # asset_deps_after = set()
        for mod_name in self._used_modules:
            asset_deps_before.update(self._store.get_associated_assets(mod_name))
        
        # Push assets in the lists (sorted by the creation time)
        f = lambda a: a.i
        for asset in reversed(sorted(asset_deps_before, key=f)):
            if asset.name.lower().endswith('.js'):
                js_assets.insert(0, asset)
            else:
                css_assets.insert(0, asset)
       
        # Mark all assets as used. For now, we only use assets that are available
        # in the asset store.
        for asset in js_assets + css_assets:
            self._assets[asset.name] = None
        
        
        # Prepend reset.css
        if css_reset:
            css_assets.insert(0, self._store.get_asset('reset.css'))
        
        # Prepend flexx-info, module loader, and pyscript std
        js_assets.insert(0, self._store.get_asset('pyscript-std.js'))
        js_assets.insert(0, self._store.get_asset('flexx-loader.js'))
        t = 'var flexx = {app_name: "%s", session_id: "%s"};'
        js_assets.insert(0, Asset('flexx-info.js', t % (self._app_name, self.id)))
        
        # Mark this session as served; all future asset loads are dynamic
        self._served = time.time()
        
        # todo: fix incorrect order; loader should be able to handle it for JS
        #import random
        #random.shuffle(js_assets)
        
        return js_assets, css_assets
    
    def get_page(self, link=3):
        """ Get the string for the HTML page to render this session's app.
        """
        js_assets, css_assets = self.get_assets_in_order(True)
        for asset in js_assets + css_assets:
            if asset.remote and asset.source.startswith('file://'):
                raise RuntimeError('Can only use remote assets with "file://" '
                                   'when exporting.')
        return self._get_page(js_assets, css_assets, link, False)
    
    def get_page_for_export(self, commands, link=0):
        """ Get the string for an exported HTML page (to run without a server).
        """
        # Create lines to init app
        lines = []
        lines.append('flexx.is_exported = true;\n')
        lines.append('flexx.runExportedApp = function () {')
        lines.extend(['    flexx.command(%s);' % reprs(c) for c in commands])
        lines.append('};\n')
        # Create a session asset for it, "-export.js" is always embedded
        export_asset = Asset('flexx-export.js', '\n'.join(lines))
        # Compose
        bundle_level = 2 if (link >= 2) else 9
        js_assets, css_assets = self.get_assets_in_order(css_reset=True,
                                                         bundle_level=bundle_level)
        js_assets.append(export_asset)
        return self._get_page(js_assets, css_assets, link, True)
    
    def _get_page(self, js_assets, css_assets, link, export):
        """ Compose index page.
        """
        pre_path = '_assets' if export else '/flexx/assets'
        
        codes = []
        for assets in [css_assets, js_assets]:
            for asset in assets:
                if not link:
                    html = asset.to_html('{}', link)
                else:
                    if asset.name.endswith(('-info.js', '-export.js')):
                        html = asset.to_html('', 0)
                    elif self._store.get_asset(asset.name) is not asset:
                        html = asset.to_html(pre_path + '/%s/{}' % self.id, link)
                    else:
                        html = asset.to_html(pre_path + '/shared/{}', link)
                codes.append(html)
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
    
    def _export(self, dirname, clear=False):
        """ Export all assets and data specific to this session.
        Private method, used by app.export().
        """
        # Note that self.id will have been set to the app name.
        assets = []
        data = [(name, self.get_data(name)) for name in self.get_data_names()]
        export_assets_and_data(assets, data, dirname, self.id, clear)
        logger.info('Exported assets and data for %r to %r.' % (self.id, dirname))


class Session(SessionAssets):
    """
    A session between Python and the client runtime.
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
        
        # A counter to generate model id's, used by the Model class
        self._modelcounter = 0
        
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
        self._ws.command('INIT-DONE')
   
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
