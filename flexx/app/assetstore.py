"""
Asset store.

The purpose of these classes is simple: they must provide the assets
(JavaScript files, CSS files, images, etc.) needed by the applications.

Assets are global, which makes certain things (e.g. exporting a bunch
of apps to the same directory) very simple.

Naturally, different sessions may need different assets with the same
name. Therefore the SessionAssets class provides a way to manage assets
with name mangling.
    
Groups of Pair classes can be added as a CSS and JS asset using
``assets.create_module_assets()``, which will select all Pair classes
present in the given Python module. Classes used by the session that
are not provided via such a module asset will be added to the index.
"""

import os
import sys
import logging
from collections import OrderedDict

from ..pyscript import py2js, clean_code
from .pair import Pair, get_pair_classes

INDEX = """<!doctype html>
<html>
<head>
    <meta charset="utf-8">
    <title>Flexx UI</title>
    
CSS-HOOK

JS-HOOK

</head>

<body id='body'>

INDEX-HOOK

</body>
</html>
"""


def modname_startswith(x, y):
    return (x + '.').startswith(y + '.')


def create_css_and_js_from_pair_classes(classes, css='', js=''):
    # Collect CSS and JS, and filter out empty ones
    css, js = [css], ['"use strict";', js]
    for cls in classes:
        css.append(cls.CSS)  # the CSS is '' if not specified for that class
        js.append(cls.JS.CODE)
    css = [i for i in css if i.strip()]
    js = [i for i in js if i.strip()]
    return '\n\n'.join(css), clean_code('\n\n'.join(js))


class AssetStore:
    """ Global provider of client assets (CSS, JavaScript, images, etc.).
    
    Assets are global to the process via the AssetStore instance at
    ``flexx.app.assets``. Use the Session instance to get unique (name
    mangled) assets.
    """
    
    def __init__(self):
        self._cache = {}
        self._assets = {}
        self._module_names = []
    
    def _cache_get(self, key):
        """ Get content using caching.
        """
        if key not in self._cache:
            if key.startswith('http://') or key.startswith('https://'):
                raise NotImplementedError('HTTP assets not supported yet')
            elif os.path.isfile(key):
                self._cache[key] = open(key, 'rb').read()
            else:  # this should never happen
                raise RuntimeError('Asset cache key is not a known module or filename: %r' % key)
        return self._cache[key]
    
    def get_asset_names(self):
        """ Get a list of all asset names (ordered alphabetically).
        """
        # Note: order matters not (it does for the session though)
        return list(sorted(self._assets.keys()))
    
    def add_asset(self, fname, content):
        """ Add an asset. Can be JavaScript, CSS, images, etc. 
        
        Parameters:
            fname (str): the (relative) filename for the asset.
            content (str, bytes): the content of the asset. If a str,
                it is interpreted as the filename to the asset (the
                contents will be cached). If bytes, it is interpreted
                as the raw asset content.
        """
        if fname in self._assets:
            if content == self._assets[fname]:
                return  # asset is the same (same filename or same bytes)
            else:
                raise ValueError('Asset %r is already set. Can only reuse if content is a filename and the same.' % fname)
        
        if isinstance(content, bytes):
            self._assets[fname] = content
        elif isinstance(content, str):
            if content.startswith('http://') or content.startswith('https://'):
                pass  # don't check now
            elif not os.path.isfile(content):
                content = content if (len(content) < 99) else content[:99] + '...'
                raise ValueError('Asset file does not exist: %r' % content)
            self._assets[fname] = content
        else:
            raise ValueError('An asset must be str or bytes.')
    
    def load_asset(self, fname):
        """ Get the asset corresponding to the given name.
        
        Parameters:
            fname (str): the (relative) filename for the asset.
        Returns:
            asset (bytes): the asset content.
        """
        try:
            content = self._assets[fname]
        except KeyError:
            raise IndexError('Asset %r not known.' % fname)
        
        if isinstance(content, str):
            return self._cache_get(content)
        else:
            return content
    
    def get_module_name_for_pair_class(self, cls):
        """ Given a Pair class, get the module name for which we have
        a corresponding asset, or None if we don't.
        """
        modname = cls.__module__
        for name in self._module_names:
            if modname_startswith(modname, name):
                return name
    
    def create_module_assets(self, module_name, css='', js=''):
        """ Create an asset with Pair classes from a Python module.
        
        Create a JS and CSS asset containing the definitions of all Pair classes
        defined in the given module.
        
        Parameters:
            module_name (str): the Python module to create a module asset for.
            css (str, optional): additional CSS to prepend to the module.
            js (str, optional): additional JS to prepend to the module.
        """
        # Collect classes and remember which ones we have covered
        classes = list()
        for cls in get_pair_classes():
            if modname_startswith(cls.__module__, module_name):
                # This cls is in our module, check if we dont already have it
                for name in self._module_names:
                    if modname_startswith(cls.__module__, name):
                        break
                else:
                    classes.append(cls)
        
        css_, js_ = create_css_and_js_from_pair_classes(classes, css, js)
        
        # Store module name and sort
        self._module_names.append(module_name)
        self._module_names.sort(key=lambda x: -len(x))
        
        # Create cached assets
        fname = module_name.replace('.', '-')
        self._assets[fname + '.css'] = css_.encode()
        self._assets[fname + '.js'] = js_.encode()


# Our singleton asset store
assets = AssetStore()


class SessionAssets:
    """ Provider for assets for a specific session. Inherited by Session.
    """
    
    def __init__(self, store=None):  # Allow custom store for testing
        self._store = store if (store is not None) else assets
        assert isinstance(self._store, AssetStore)
        self._asset_names = list()
        self._served = False
        self._known_classes = set()  # Cache what classes we know (for performance)
        self._extra_pair_classes = []  # Pair classes that are not in an asset/module
    
    @property
    def id(self):
        """ The unique identifier of this session.
        """
        return '%x' % id(self)
    
    def get_used_asset_names(self):
        """ Get a list of names of the assets used by this session, in
        the order that they were added.
        """
        return list(self._asset_names)  # Note: order matters
    
    def use_asset(self, fname):
        """ Make this session use the given asset.
        
        The given asset must be available in the asset store
        (``app.assets``). JS and CSS assets are added/linked in the
        page index.
        
        Parameters:
            fname (str): the (relative) filename for the asset.
        """
        if fname not in self._store.get_asset_names():
            raise IndexError('Asset %r is not present in the store.' % fname)
        
        if self._served and (fname.endswith('.js') or fname.endswith('.css')):
            logging.warn('Adding asset %r but the page has already been "served".' % fname)
        
        if fname not in self._asset_names:
            self._asset_names.append(fname)
    
    def add_asset(self, fname, content):
        """ Add an asset specific for this session.
        
        Assets are global to the process (stored in AssetStore
        ``app.assets``), which is why the ``fname`` is mangled with the
        session id.
        
        Parameters:
            fname (str): the (relative) filename for the asset.
            content (str, bytes): the content of the asset. If a str,
                it is interpreted as the filename to the asset. If
                bytes, it is interpreted as the raw asset content.
        Returns:
            fname (str): A mangled version of the given ``fname``.
        """
        part1, dot, part2 = fname.rpartition('.')
        fname = '%s-%s%s%s' % (part1, self.id, dot, part2)
        self.add_global_asset(fname, content)
        return fname
    
    def add_global_asset(self, fname, content):
        """ Add an asset that is global to this process.
        
        Use this for JS and CSS, but probably not for images and content
        specific for a certain app. This is equivalent to
        ``app.assets.add_asset(fname, content)`` followed  by
        ``session.use_asset(fname)``.
        """
        self._store.add_asset(fname, content)
        self.use_asset(fname)
    
    def _register_pair_class(self, cls):
        """ Ensure that the client knows the given class. A class can
        already be defined via a module asset, or we can add it to a
        pending list if the page has not been served yet. Otherwise it
        needs to be defined dynamically.
        """
        if not (isinstance(cls, type) and issubclass(cls, Pair)):
            raise ValueError('Not a Pair class')
        
        # Early exit if we know the class already
        if cls in self._known_classes:
            return
        
        # Make sure the base classes are registered first
        for cls2 in cls.mro()[1:]:
            if not issubclass(cls2, Pair):  # True if cls2 is *the* Pair class
                break
            if cls2 not in self._known_classes:
                self._register_pair_class(cls2)
        
        self._known_classes.add(cls)
        
        # Check if cls is covered by our assets
        module_name = self._store.get_module_name_for_pair_class(cls)
        if module_name:
            # cls is present in a module, add corresponding asset (overwrite ok)
            fname = module_name.replace('.', '-')
            if (fname + '.js') not in self._asset_names:
                self.use_asset(fname + '.css')
                self.use_asset(fname + '.js')
        elif not self._served:
            # Remember cls, will be served in the index
            self._extra_pair_classes.append(cls)
        else:
            # Define class dynamically - assuming we're a session subclass ...
            logging.warn('Dynamically defining class %r' % cls)
            js, css = cls.JS.CODE, cls.CSS
            self._send_command('DEFINE-JS ' + js)
            if css.strip():
                self._send_command('DEFINE-CSS ' + css)
    
    def _get_js_and_css_assets(self):
        """ Get an ordered dictionary with the JS and CSS assets.
        """
        # Create assets from our extra pair classes
        if self._extra_pair_classes:
            css, js = create_css_and_js_from_pair_classes(self._extra_pair_classes)
            self.add_asset('index-extra-pair-classes.css', css.encode())
            self.add_asset('index-extra-pair-classes.js', js.encode())
        self._extra_pair_classes = None  # make sure we wont append to it anymore :)
        # Mark that any new assets dont make it into the currently served page
        self._served = True
        # Collect assets
        d = OrderedDict()
        for fname in self.get_used_asset_names():
            if fname.endswith('.js') or fname.endswith('.css'):
                d[fname] = self._store.load_asset(fname).decode()
        return d
    
    def get_all_css_and_js(self):
        """ Get a string with all css and a string with all JS.
        """
        css, js = [], []
        for fname, code in self._get_js_and_css_assets().items():
            if fname.endswith('.css'):
                css.append(code)
            elif fname.endswith('.js'):
                js.append(code)
            
        return '\n\n'.join(css), '\n\n'.join(js)
    
    def get_page(self, single=False):
        """ Get the string for the HTML page to render this session's app.
        """
        return self._get_page(single)
    
    def get_page_for_export(self, commands, single=False):
        """ Get the string for an exported HTML page (to run without a server).
        """
        # Create lines to init app
        lines = []
        lines.append('flexx.is_exported = true;\n')
        lines.append('flexx.runExportedApp = function () {')
        lines.extend(['    flexx.command(%r);' % c for c in commands])
        lines.append('};\n')
        
        # Create an extra asset for the export
        self.add_asset('index-export.js', '\n'.join(lines).encode())
        return self._get_page(single)
    
    def _get_page(self, single):
        """ This code takes the template, the collected JS and CSS, and
        composes an index page to serve/export.
        """
        # Init source code from template
        js_elements = []  # links to external JS docs
        css_elements = []  # links to external CSS docs
        index_elements = []  # code to put in the index
        
        # Collect JS and CSS
        for fname, code in self._get_js_and_css_assets().items():
            if not code.strip():  # pragma: no cover
                continue
            if single or fname.startswith('index-'):
                if fname.endswith('.css'):
                    css = "<style>\n/* CSS for %s */\n%s\n</style>" % (fname, code)
                    index_elements.append(css)
                else:
                    js = "<script>\n/* JS for %s */\n%s\n</script>" % (fname, code)
                    index_elements.append(js)
            else:
                if fname.endswith('.css'):
                    css = "    <link rel='stylesheet' type='text/css' href='%s' />" % fname
                    css_elements.append(css)
                else:
                    js = "    <script src='%s'></script>" % fname
                    js_elements.append(js)
        
        # Compose index page
        src = INDEX
        src = src.replace('JS-HOOK', '\n'.join(js_elements))
        src = src.replace('CSS-HOOK', '\n'.join(css_elements))
        src = src.replace('INDEX-HOOK', '\n'.join(index_elements))
        
        return src
