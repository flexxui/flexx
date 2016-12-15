"""
Flexx asset and data management system. The purpose of this class
is to provide the assets (JavaScript and CSS files) and data (images,
etc.) needed by the applications.
"""

import os
import shutil

from ..pyscript import create_js_module, get_all_std_names, get_full_std_lib

from ._model import Model
from ._asset import Asset, Bundle, HEADER
from ._modules import JSModule
from . import logger


INDEX = """
<!doctype html>
<html>
<head>
    <meta charset="utf-8">
    <title>Flexx UI</title>
</head>

<body id='body'>

<div class='flx-spinner' style='position:absolute; top:25%; bottom:25%;
left:25%; right:25%; background:#fff; color:#555; text-align:center;
word-break: break-all; border-radius:0.5em; padding:0.5em;'>
Starting Flexx app <div style='font-size:50%; color:#66A;'></div>
</div>

ASSET-HOOK

</body>
</html>
""".lstrip()

# This is our loader for AMD modules. It invokes the modules immediately and
# does not resolve dependency order, since the server takes care of that and
# we want Flexx to be ready to use so we can execute commands via the
# websocket. It also allows redefining modules so that one can interactively
# (re)define module classes. The loader is itself wrapped in a IIFE to
# create a private namespace. The modules must follow this pattern:
# define(name, dep_strings, function (name1, name2) {...});

LOADER = """
/*Flexx module loader. Licensed by BSD-2-clause.*/

(function(){

if (typeof window === 'undefined' && typeof module == 'object') {
    throw Error('flexx.app does not run on NodeJS!');
}
if (typeof flexx == 'undefined') {
    window.flexx = {};
}

var modules = {};
function define (name, deps, factory) {
    if (arguments.length == 1) {
        factory = name;
        deps = [];
        name = null;
    }
    if (arguments.length == 2) {
        factory = deps;
        deps = name;
        name = null;
    }
    // Get dependencies - in current implementation, these must be loaded
    var dep_vals = [];
    for (var i=0; i<deps.length; i++) {
        if (modules[deps[i]] === undefined) {
            throw Error('Unknown dependency: ' + deps[i]);
        }
        dep_vals.push(modules[deps[i]]);
    }
    // Load the module and store it if is not anonymous
    var mod = factory.apply(null, dep_vals);
    if (name) {
        modules[name] = mod;
    }
}
define.amd = true;
define.flexx = true;

function require (name) {
    if (name.startsWith('phosphor/')) {
        if (window.jupyter && window.jupyter.lab && window.jupyter.lab.loader) {
            var path = 'phosphor@*/' + name.slice(9);
            if (!path.endsWith('.js')) { path = path + '.js'; }
            return window.jupyter.lab.loader.require(path);
        } else {
            return window.require_phosphor(name);  // provided by our Phosphor-all
        }
    }
    if (modules[name] === undefined) {
        throw Error('Unknown module: ' + name);
    }
    return modules[name];
}

// Expose this
window.flexx.define = define;
window.flexx.require = require;
window.flexx._modules = modules;

})();
""".lstrip()

RESET = """
/*! normalize.css v3.0.3 | MIT License | github.com/necolas/normalize.css */
html
{font-family:sans-serif;-ms-text-size-adjust:100%;-webkit-text-size-adjust:100%}
body{margin:0}
article,aside,details,figcaption,figure,footer,header,hgroup,main,menu,nav,
section,summary{display:block}
audio,canvas,progress,video{display:inline-block;vertical-align:baseline}
audio:not([controls]){display:none;height:0}
[hidden],template{display:none}
a{background-color:transparent}
a:active,a:hover{outline:0}
abbr[title]{border-bottom:1px dotted}
b,strong{font-weight:bold}
dfn{font-style:italic}
h1{font-size:2em;margin:.67em 0}
mark{background:#ff0;color:#000}
small{font-size:80%}
sub,sup{font-size:75%;line-height:0;position:relative;vertical-align:baseline}
sup{top:-0.5em}
sub{bottom:-0.25em}
img{border:0}
svg:not(:root){overflow:hidden}
figure{margin:1em 40px}
hr{box-sizing:content-box;height:0}
pre{overflow:auto}
code,kbd,pre,samp{font-family:monospace,monospace;font-size:1em}
button,input,optgroup,select,textarea{color:inherit;font:inherit;margin:0}
button{overflow:visible}
button,select{text-transform:none}
button,html input[type="button"],input[type="reset"],input[type="submit"]
{-webkit-appearance:button;cursor:pointer}
button[disabled],html input[disabled]{cursor:default}
button::-moz-focus-inner,input::-moz-focus-inner{border:0;padding:0}
input{line-height:normal}
input[type="checkbox"],input[type="radio"]{box-sizing:border-box;padding:0}
input[type="number"]::-webkit-inner-spin-button,
input[type="number"]::-webkit-outer-spin-button{height:auto}
input[type="search"]{-webkit-appearance:textfield;box-sizing:content-box}
input[type="search"]::-webkit-search-cancel-button,
input[type="search"]::-webkit-search-decoration{-webkit-appearance:none}
fieldset{border:1px solid #c0c0c0;margin:0 2px;padding:.35em .625em .75em}
legend{border:0;padding:0}
textarea{overflow:auto}
optgroup{font-weight:bold}
table{border-collapse:collapse;border-spacing:0}
td,th{padding:0}
""".lstrip()


def export_assets_and_data(assets, data, dirname, app_id, clear=False):
    """ Export the given assets (list of Asset objects) and data (list of
    (name, value) tuples to a file system structure.
    """
    # Normalize and check - we create the dir if its inside an existing dir
    dirname = os.path.abspath(os.path.expanduser(dirname))
    if clear and os.path.isdir(dirname):
        shutil.rmtree(dirname)
    if not os.path.isdir(dirname):
        if os.path.isdir(os.path.dirname(dirname)):
            os.mkdir(dirname)
        else:
            raise ValueError('dirname %r for export is not a directory.' % dirname)
    
    # Export all assets
    for asset in assets:
        filename = os.path.join(dirname, '_assets', app_id, asset.name)
        dname = os.path.dirname(filename)
        if not os.path.isdir(dname):
            os.makedirs(dname)
        with open(filename, 'wb') as f:
            f.write(asset.to_string().encode())
    
    # Export all data
    for fname, d in data:
        filename = os.path.join(dirname, '_data', app_id, fname)
        dname = os.path.dirname(filename)
        if not os.path.isdir(dname):
            os.makedirs(dname)
        with open(filename, 'wb') as f:
            f.write(d)


class AssetStore:
    """
    Provider of shared assets (CSS, JavaScript) and data (images, etc.).
    Keeps track of JSModules and makes them available via asset bundles.
    The global asset store object can be found at ``flexx.app.assets``.
    Assets and data in the asset store can be used by all sessions.
    Each session object also keeps track of data. 
    
    Assets with additional JS or CSS to load can be used simply by
    creating/importing them in a module that defines the Model class
    that needs the asset.
    """
    
    def __init__(self):
        self._known_model_classes = set()
        self._modules = {}
        self._assets = {}
        self._associated_assets = {}
        self._data = {}
        self._used_assets = set()  # between all sessions (for export)
        
        # Create standard assets
        asset_reset = Asset('reset.css', RESET)
        asset_loader = Asset('flexx-loader.js', LOADER)
        func_names, method_names = get_all_std_names()
        mod = create_js_module('pyscript-std.js', get_full_std_lib(),
                               [], func_names + method_names, 'amd-flexx')
        asset_pyscript = Asset('pyscript-std.js', HEADER + mod)
        
        # Add them
        for a in [asset_reset, asset_loader, asset_pyscript]:
            self.add_shared_asset(a)
        
        if getattr(self, '_test_mode', False):
            return
        
        #  Create flexx-core bootstrap bundle
        self.update_modules()  # to collect _model and _clientcore
        asset_core = Bundle('flexx-core.js')
        asset_core.add_asset(asset_loader)
        asset_core.add_asset(asset_pyscript)
        asset_core.add_module(self.modules['flexx.app._clientcore'])
        asset_core.add_module(self.modules['flexx.app._model'])
        self.add_shared_asset(asset_core)
    
    def __repr__(self):
        t = '<AssetStore with %i assets, and %i data>'
        return t % (len(self._assets), len(self._data))
    
    def create_module_assets(self, *args, **kwargs):
        # Backward compatibility
        raise RuntimeError('create_module_assets is deprecated and no '
                           'longer necessary.')
    
    @property
    def modules(self):
        """ The JSModule objects known to the asset store. Each module
        corresponds to a Python module.
        """
        return self._modules
    
    def update_modules(self):
        """ Collect and update the JSModule instances that correspond
        to Python modules that define Model classes. Any newly created
        modules get added to all corresponding assets bundles (creating
        them if needed).
        
        It is safe (and pretty fast) to call this more than once since
        only missing modules are added. This gets called automatically
        by the Session object.
        """
        
        # Dependencies can drag in more modules, therefore we store
        # what modules we know of beforehand.
        current_module_names = set(self._modules)
        
        # Track all known (i.e. imported classes) Model classes. We keep track
        # of what classes we've registered, so this is pretty efficient. This
        # works also if a module got a new or renewed Model class.
        for cls in Model.CLASSES:
            if cls not in self._known_model_classes:
                self._known_model_classes.add(cls)
                if cls.__jsmodule__ not in self._modules:
                    JSModule(cls.__jsmodule__, self._modules)  # auto-registers
                self._modules[cls.__jsmodule__].add_variable(cls.__name__)
        
        # Deal with new modules: store asset deps and bundle the modules
        mcount = 0
        bcount = 0
        for name in set(self._modules).difference(current_module_names):
            mod = self.modules[name]
            mcount += 1
            # Get names of bundles to add this module to
            bundle_names = []
            bundle_names.append(name)  # bundle of exactly this one module
            while '.' in name:
                name = name.rsplit('.', 1)[0]
                bundle_names.append(name)
            bcount += len(bundle_names)
            # Add to bundles, create bundle if necesary
            for name in bundle_names:
                for suffix in ['.js', '.css']:
                    bundle_name = name + suffix
                    if bundle_name not in self._assets:
                        self._assets[bundle_name] = Bundle(bundle_name)
                    self._assets[bundle_name].add_module(mod)
        
        if mcount:
            logger.info('Asset store collected %i new modules.' % mcount)
    
    def get_asset(self, name):
        """ Get the asset instance corresponding to the given name or None
        if it not known.
        """
        if not name.lower().endswith(('.js', '.css')):
            raise ValueError('Asset names always end in .js or .css')
        try:
            asset = self._assets[name]
        except KeyError:
            raise KeyError('Asset %r is not available in the store.' % name)
        self._used_assets.add(asset.name)
        return asset
    
    def get_data(self, name):
        """ Get the data (as bytes) corresponding to the given name or None
        if it not known.
        """
        return self._data.get(name, None)
    
    def get_asset_names(self):
        """ Get a list of all asset names.
        """
        return list(self._assets.keys())
    
    def get_data_names(self):
        """ Get a list of all data names.
        """
        return list(self._data.keys())
    
    def add_shared_asset(self, asset_name, source=None):
        """ Add an asset to the store so that the client can load it from the
        server. Users typically only need this to provide an asset without
        loading it in the main page, e.g. when the asset is loaded by a
        secondary page, a web worker, or AJAX.
        
        Parameters:
            name (str): the asset name, e.g. 'foo.js' or 'bar.css'. Can contain
                slashes to emulate a file system. e.g. 'spam/foo.js'. If a URL
                is given, both name and source are implicitly set (and its
                a remote asset).
            source (str, function): the source for this asset. Can be:
            
                * The source code.
                * A URL (str starting with 'http://' or 'https://'),
                  making this a "remote asset". Note that ``app.export()``
                  provides control over how (remote) assets are handled.
                * A funcion that should return the source code, and which is
                  called only when the asset is used. This allows defining
                  assets without causing side effects when they're not used.
        
        Returns:
            url: the (relative) url at which the asset can be retrieved.
            
        """
        if isinstance(asset_name, Asset):
            # undocumented feature; users will rarely use Asset objects
            asset = asset_name
        else:
            asset = Asset(asset_name, source)
        if asset.name in self._assets:
            raise ValueError('Asset %r already registered.' % asset.name)
        self._assets[asset.name] = asset
        # Returned url is relative so that it also works in exported apps.
        # The server will redirect this to /flexx/assets/shared/...
        return '_assets/shared/' + asset.name
    
    def associate_asset(self, mod_name, asset_name, source=None):
        """ Associate an asset with the given module.
        The assets will be loaded when the module that it is associated with
        is used by JavaScript. Multiple assets can be associated with
        a module, and an asset can be associated with multiple modules.
        
        The intended usage is to write the following inside a module that needs
        the asset: ``app.assets.associate_asset(__name__, ...)``.
        
        Parameters:
            mod_name (str): The name of the module to associate the asset with.
            asset_name (str): The name of the asset to associate. Can be an
                already registered asset, or a new asset.
            source (str, callable, optional): The source for a new asset. See
                ``add_shared_asset()`` for details. It is an error to supply a
                source if the asset_name is already registered.
        
        Returns:
            url: the (relative) url at which the asset can be retrieved.
        """
        # Get or create asset
        if asset_name in self._assets:
            asset = self._assets[asset_name]
            if source is not None:
                t = 'associate_asset() for %s got source, but asset %r already exists.'
                raise TypeError(t % (mod_name, asset_name))
        else:
            asset = Asset(asset_name, source)
            self.add_shared_asset(asset)
        # Add to the list of assets for this module
        assets = self._associated_assets.setdefault(mod_name, [])
        if asset.name not in [a.name for a in assets]:
            assets.append(asset)
            assets.sort(key=lambda x: x.i)  # sort by instantiation time
        return '_assets/shared/' + asset.name
    
    def get_associated_assets(self, mod_name):
        """ Get the names of the assets associated with the given module name.
        Sorted by instantiation time.
        """
        assets = self._associated_assets.get(mod_name, [])
        return tuple([a.name for a in assets])
    
    def add_shared_data(self, name, data):
        """ Add data to serve to the client (e.g. images), which is shared
        between sessions. It is an error to add data with a name that is
        already registered. See ``Session.add_data()`` to set data per-session
        and `Model.send_data()`` to send data to Model objects directly.
        
        Parameters:
            name (str): the name of the data, e.g. 'icon.png'. 
            data (bytes): the data blob.
        
        Returns:
            url: the (relative) url at which the data can be retrieved.
        
        """
        if not isinstance(name, str):
            raise TypeError('add_shared_data() name must be a str.')
        if name in self._data:
            raise ValueError('add_shared_data() got existing name %r.' % name)
        if not isinstance(data, bytes):
            raise TypeError('add_shared_data() data must be bytes.')
        self._data[name] = data
        return '_data/shared/%s' % name  # relative path so it works /w export
    
    def export(self, dirname, clear=False):
        """ Write all shared data and used assets to the given directory.
        
        Parameters:
            dirname (str): the directory to export to. The toplevel
                directory is created if necessary.
            clear (bool): if given and True, the directory is first cleared.
        """
        assets = [self._assets[name] for name in self.get_asset_names()]
        assets = [self._assets[name] for name in self._used_assets]
        data = [(name, self.get_data(name)) for name in self.get_data_names()]
        export_assets_and_data(assets, data, dirname, 'shared', clear)
        logger.info('Exported shared assets and data to %r.' % dirname)


# Our singleton asset store
assets = AssetStore()
