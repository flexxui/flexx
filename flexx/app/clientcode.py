"""
This module defined the client PyScript code to handle the connection
with the Python server.

Further, it defines a (singleton) class that can collects all the
JS/CSS, and provides this client code (HTML/JS/CSS) in diffent ways.
This streamlines the inclusion in Jupyter and our export mechanism.
"""

import os
import logging
from collections import OrderedDict

from ..pyscript import py2js, clean_code
from ..util.minify import minify

# todo: minification

# todo: notes on caching:
# We should provide a means to efficiently cache indidifual JSObjects
# in a file on disk. Doing this woul automatically speed up the
# collect() method of clientCode. We could also cache flexx.js et. al.
# to disk, but its not straightforward to detect when the cache is not
# valid anymore (source has changed), also, with the caching mechanism
# above it might not be necessary. Therefore, the flexx.js et al. will
# probably only be written to disk for export.


THIS_DIR = os.path.abspath(os.path.dirname(__file__))
HTML_DIR = os.path.join(os.path.dirname(THIS_DIR), 'html')

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


@py2js
class FlexxJS:
    """ JavaScript Flexx module. This provides the connection between
    the Python and JS (via a websocket).
    """
    
    def __init__(self):
        
        self.ws = None
        self.last_msg = None
        self.is_notebook = False  # if not, we "close" when the ws closes
        # For nodejs, the location is set by the flexx nodejs runtime.
        self.ws_url = ('ws://%s:%s/%s/ws' % (location.hostname, location.port, 
                                             location.pathname))
        self.is_exported = False
        self.classes = {}
        self.instances = {}
        if typeof(window) is 'undefined' and typeof(module) is 'object':
            # nodejs (call exit on exit and ctrl-c
            self._global = root
            self.nodejs = True
            root.setTimeout(self.init, 1)  # ms
            process.on('exit', self.exit, False)
            process.on('SIGINT', self.exit, False)
            root.setTimeout(self.exit, 10000000)  # keep alive ~35k years
        else:
            # browser
            self._global = window
            window.addEventListener('load', self.init, False)
            window.addEventListener('beforeunload', self.exit, False)
    
    def init(self):
        """ Called after document is loaded. """
        if flexx.is_exported:
            flexx.runExportedApp()
        elif flexx.is_notebook and not (window.IPython and 
                                        window.IPython.notebook and 
                                        window.IPython.notebook.session):
            print('Hey, I am in an exported notebook!')
        else:
            flexx.initSocket()
            flexx.initLogging()
        
    def exit(self):
        """ Called when runtime is about to quit. """
        if self.ws:  # is not null or undefined
            self.ws.close()
            self.ws = None
    
    def get(self, id):
        """ Get instance of a Pair class.
        """
        if id == 'body':
            return document.body
        else:
            return self.instances[id]
    
    def initSocket(self):
        """ Make the connection to Python.
        """
        
        # Check WebSocket support
        if self.nodejs:
            try:
                WebSocket = require('ws')  # does not work on Windows?
                #WebSocket = require('websocket').client
            except Exception:
                # Better error message
                raise "FAIL: you need to 'npm install -g ws'."
        else:
            WebSocket = window.WebSocket
            if (window.WebSocket is undefined):
                document.body.innerHTML = 'This browser does not support WebSockets'
                raise "FAIL: need websocket"
        # Open web socket in binary mode
        self.ws = ws = WebSocket(flexx.ws_url)
        ws.binaryType = "arraybuffer"
        
        def on_ws_open(evt):
            console.info('Socket connected')
        def on_ws_message(evt):
            flexx.last_msg = evt.data or evt
            msg = flexx.decodeUtf8(flexx.last_msg)
            flexx.command(msg)
        def on_ws_close(evt):
            self.ws = None
            msg = 'Lost connection with server'
            if evt and evt.reason:  # nodejs-ws does not have it?
                msg += ': %s (%i)' % (evt.reason, evt.code)
            if (not flexx.is_notebook) and (not self.nodejs):
                document.body.innerHTML = msg
            else:
                console.info(msg)
        def on_ws_error(self, evt):
            self.ws = None
            if flexx.is_notebook:
                console.error('Socket error: re-run flexx.app.init_socket() to connect.')
            else:
                console.error('Socket error')
        
        # Connect
        if self.nodejs:
            ws.on('open', on_ws_open)
            ws.on('message', on_ws_message)
            ws.on('close', on_ws_close)
            ws.on('error', on_ws_error)
        else:
            ws.onopen = on_ws_open
            ws.onmessage = on_ws_message
            ws.onclose = on_ws_close
            ws.onerror  = on_ws_error
    
    def initLogging(self):
        """ Setup logging so that messages are proxied to Python.
        """
        if console.ori_log:
            return  # already initialized the loggers
        # Keep originals
        console.ori_log = console.log
        console.ori_info = console.info or console.log
        console.ori_warn = console.warn or console.log
        console.ori_error = console.error or console.log
        
        def log(self, msg):
            console.ori_log(msg)
            if flexx.ws is not None: flexx.ws.send("PRINT " + msg)
        def info(self, msg):
            console.ori_info(msg)
            if flexx.ws is not None: flexx.ws.send("INFO " + msg)
        def warn(self, msg):
            console.ori_warn(msg)
            if flexx.ws is not None: flexx.ws.send("WARN " + msg)
        def error(self, msg):
            console.ori_error(msg)
            if flexx.ws is not None: flexx.ws.send("ERROR " + msg)
        def on_error(self, evt):
            msg = evt
            if evt.message and evt.lineno:  # message, url, linenumber (not in nodejs)
                msg = "On line %i in %s:\n%s" % (evt.lineno, evt.filename, evt.message)
            elif evt.stack:
                msg = evt.stack
            if flexx.ws is not None: flexx.ws.send("ERROR " + msg)
        
        # Set new versions
        console.log = log
        console.info = info
        console.warn = warn
        console.error = error
        # Create error handler, so that JS errors get into Python
        if self.nodejs:
            process.on('uncaughtException', on_error, False)
        else:
            window.addEventListener('error', on_error, False)
    
    def command(self, msg):
        """ Execute a command received from the server.
        """
        if msg.startswith('PRINT '):
            console.ori_log(msg[6:])
        elif msg.startswith('EVAL '):
            self._global._ = eval(msg[5:])
            flexx.ws.send('RET ' + self._global._)  # send back result
        elif msg.startswith('EXEC '):
            eval(msg[5:])  # like eval, but do not return result
        elif msg.startswith('DEFINE-JS '):
            eval(msg[10:])
            #el = document.createElement("script")
            #el.innerHTML = msg[10:]
            #document.body.appendChild(el)
        elif msg.startswith('DEFINE-CSS '):
            # http://stackoverflow.com/a/707580/2271927
            el = document.createElement("style")
            el.type = "text/css"
            el.innerHTML = msg[11:]
            document.body.appendChild(el)
        elif msg.startswith('TITLE '):
            if not self.nodejs:
                document.title = msg[6:]
        elif msg.startswith('ICON '):
            if not self.nodejs:
                link = document.createElement('link')
                link.rel = 'icon'
                link.href = msg[5:]
                document.head.appendChild(link)
                #document.getElementsByTagName('head')[0].appendChild(link);
        elif msg.startswith('OPEN '):
            window.win1 = window.open(msg[5:], 'new', 'chrome')
        else:
            console.warn('Invalid command: "' + msg + '"')
    
    def decodeUtf8(self, arrayBuffer):
        """
        var result = "",
            i = 0,
            c = 0,
            c1 = 0,
            c2 = 0,
            c3 = 0,
            data = new Uint8Array(arrayBuffer);
    
        // If we have a BOM skip it
        if (data.length >= 3 && data[0] === 0xef && data[1] === 0xbb && data[2] === 0xbf) {
            i = 3;
        }
    
        while (i < data.length) {
            c = data[i];
    
            if (c < 128) {
                result += String.fromCharCode(c);
                i += 1;
            } else if (c > 191 && c < 224) {
                if (i + 1 >= data.length) {
                    throw "UTF-8 Decode failed. Two byte character was truncated.";
                }
                c2 = data[i + 1];
                result += String.fromCharCode(((c & 31) << 6) | (c2 & 63));
                i += 2;
            } else {
                if (i + 2 >= data.length) {
                    throw "UTF-8 Decode failed. Multi byte character was truncated.";
                }
                c2 = data[i + 1];
                c3 = data[i + 2];
                result += String.fromCharCode(((c & 15) << 12) | ((c2 & 63) << 6) | (c3 & 63));
                i += 3;
            }
        }
        return result;
        """

# todo: rename to asset store?
class ClientCode(object):
    """
    This class provides means to deliver client code (HTML/JS/CSS) to
    the web runtime, or export an app for running it later. It can
    handle a variety of delivery methods and operate in multiple
    different modes. There is only one instance of this class per
    process.
    
    Delivery method:
    
    * serve: serving an app via Tornado; the "default" behavior.
    * notebook: serve via the Jupyter notebook.
    * export: export an app to an HTML file.
    
    Modes:
    
    * split (default): the JS/CSS is served via different files.
    * single: everything is served via a single page. Intended for
      exporing apps as single files.
    
    Note that any Pair classes defined once the first connects
    will be dynamically defined, regardless of the chosen mode (after
    all, the page will already have been served).
    
    """
    
    _instance = None
    
    def __init__(self):
        
        # Enforce singleton
        if ClientCode._instance is not None:
            raise RuntimeError('ClientCode must be singleton')
        ClientCode._instance = self
        
        self._served = False
        
        # Assets - a JS or CSS asset named 'index-X' will appear in the index
        self._assets = OrderedDict()
        # self._files = OrderedDict()  # files are assets to load dynamically
        # self._cache = {}  # content in files can be cached
        # self._remote_assets = OrderedDict()
        
        self._preloaded_pair_classes = set()
    
    def _collect(self, serve=True):
        """ The first time this is called, all existing Pair classes
        are collected, and their JS and CSS extracted. Any further calls
        to this method have no effect. This method is called upon app
        creation.
        
        The collected JS and CSS will be served via HTML; any Pair
        classes that are used later on will be dynamically defined (i.e.
        injected) via the websocket interface.
        """
        if self._preloaded_pair_classes:
            return
        
        # Collect JS from pair classes
        from .pair import get_pair_classes
        preloaded_pair_classes = set()
        
        js, css  = OrderedDict(), OrderedDict()
        for key in ('flexx-core', 'flexx-ui', 'index-flexx'):
            js[key], css[key] = ['"use strict;"'], []
        
        # Include Flexx object (that does communication, etc.)
        js['flexx-core'].append(FlexxJS)
        js['flexx-core'].append('var flexx = new FlexxJS();\n')
        
        # Include all pair classes, separate core, ui and other
        for cls in get_pair_classes():
            preloaded_pair_classes.add(cls)
            if cls.__module__.startswith('flexx.app'):
                key = 'flexx-core'
            elif cls.__module__.startswith('flexx.ui'):
                key = 'flexx-ui'
            else:
                key = 'index-flexx'
            js[key].append(cls.JS.CODE)
            css[key].append(cls.CSS)  # the CSS is '' if not specified for that class
        
        # Add what we collected
        for key in js:
            code = '\n\n'.join(js[key])
            code = clean_code(code)  # clear duplicate pyscript helper functions
            self.add_asset(key+'.js', code)
        for key in css:
            self.add_asset(key+'.css', '\n\n'.join(css[key]))
        
        # Wrap up
        self._preloaded_pair_classes.update(preloaded_pair_classes)
        if serve:
            self._served = True
    
    def get_defined_pair_classes(self):
        """ Get a list of all Pair classes that will be defined
        by serving the JS/CSS code.
        """
        self._collect(False)
        return self._preloaded_pair_classes
    
    def add_asset(self, fname, content):
        """ Add an asset. Can be JavaScript, CSS, images, etc. If this
        is a JS or CSS asset, it is loaded automatically (if added
        before the first app instance is created).
        """
        if fname in self._assets:
            raise ValueError('Asset %r is already set.' % fname)
        if self._served and (fname.endswith('.js') or fname.endswith('.css')):
            logging.warn('Adding asset %r but the page has already been "served".' % fname)
        self._assets[fname] = content
    
    def load(self, fname):
        """ Get the source of the given file as a string. Can be str
        or bytes.
        """
        try:
            content = self._assets[fname]
        except IndexError:
            raise ValueError('Asset %r not known.' % fname)
        
        if isinstance(content, str):
            if content.startswith('file://'):
                content_fname = content[7:]
                content = open(content_fname, 'rb').read()
                # self._assets[fname] = content  # cache
            elif content.startswith('http://') or content.startswith('https://'):
                raise NotImplementedError('HTTP assets not supported yet')
        
        return content
    
    def get_all_js(self):
        """ Get all JavaScript as a single string.
        """
        self._collect()
        parts = []
        for fname in self._assets:
            if fname.endswith('.js'):
                parts.append(self.load(fname))
        return '\n\n'.join(parts)
    
    def get_all_css(self):
        """ Get all CSS as a single string.
        """
        self._collect()
        parts = []
        for fname in self._assets:
            if fname.endswith('.css'):
                parts.append(self._assets[fname])
        return '\n\n'.join(parts)
    
    def get_js_and_css_assets(self):
        """ Get a dictionary with the JS and CSS assets needed by a
        page acquired in non-single mode.
        """
        self._collect()
        d = {}
        for fname in self._assets:
            if fname.startswith('index-'):
                continue
            if fname.endswith('.js') or fname.endswith('.css'):
                d[fname] = self.load(fname)
        return d
    
    def get_page(self, single=False):
        """ Get the string for an HTML page that can show a Flexx app.
        """
        self._collect()
        return self._get_page(single)
    
    def get_page_for_export(self, commands, single=False):
        """ Get the string for a single exported HTML page.
        """
        self._collect()
        # Create lines to init app
        lines = []
        lines.append('flexx.is_exported = true;\n')
        lines.append('flexx.runExportedApp = function () {')
        lines.extend(['    flexx.command(%r);' % c for c in commands])
        lines.append('};\n')
        
        # Create a temporary extra element
        fname = 'index-export.js'
        self._assets[fname] = '\n'.join(lines)
        try:
            return self._get_page(single)
        finally:
            self._assets.pop(fname)
    
    def _get_page(self, single):
        """ This code takes the template, the collected JS and CSS, and
        composes an index page to serve/export.
        """
        
        # Init source code from template
        js_elements = []  # links to external JS docs
        css_elements = []  # links to external CSS docs
        index_elements = []  # code to put in the index
        
        # Collect JS and CSS
        for fname in self._assets:
            if fname.endswith('.js') or fname.endswith('.css'):
                code = self.load(fname)
                if not code.strip():
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


# Create the one instance of this class. We cannot have one object
# per app, since server.py needs get_page() before there is an app.
clientCode = ClientCode()


class Exporter(object):
    """ Object that can be used by an app inplace of the websocket to
    export apps to standalone HTML. The object tracks the commands send
    by the app, so that these can be re-played in the exported document.
    """
    
    def __init__(self, proxy):
        self._commands = []
        self.close_code = None  # simulate web socket
        
        # todo: how to export icons
        self.command('ICON %s.ico' % proxy.id)
        self.command('TITLE %s' % proxy._runtime_kwargs.get('title', 'Exported flexx app'))
    
    def command(self, cmd):
        self._commands.append(cmd)
    
    def write_html(self, filename, single=True):
        """ Write html document to the given file.
        """
        if filename.startswith('~'):
            filename = os.path.expanduser(filename)
        html = self.to_html(single)
        open(filename, 'wt', encoding='utf-8').write(html)
        print('Exported app to %r' % filename)
    
    def write_dependencies(self, dirname):
        """ Write dependencies to the given dir (if a path to a file
        is given, will write to the same directory as that file). Use
        this if you export using ``single == False``.
        """
        if dirname.startswith('~'):
            dirname = os.path.expanduser(dirname)
        if os.path.isfile(dirname):
            dirname = os.path.dirname(dirname)
        for fname, content in clientCode.get_js_and_css_assets().items():
            open(os.path.join(dirname, fname), 'wt', encoding='utf-8').write(content)
    
    def to_html(self, single=True):
        """ Get the HTML string.
        """
        html = clientCode.get_page_for_export(self._commands, single)
        return html  # todo: minify somewhere ...
