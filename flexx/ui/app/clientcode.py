"""
This module defined the client PyScript code to handle the connection
with the Python server.

Further, it defines a (singleton) class that can collects all the
JS/CSS, and provides this client code (HTML/JS/CSS) in diffent ways.
This streamlines the inclusion in Jupyter and our export mechanism.
"""

import os
from collections import OrderedDict

from ...pyscript import js

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

<body id='body'></body>

</html>
"""



@js
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
        self.widgets = {}
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
        """ Get instance of a Mirrored class.
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
                raise "FAIL: you need to 'npm install ws'."
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
            msg = 'Lost connection with server'
            if evt and evt.reason:  # nodejs-ws does not have it?
                msg += ': %s (%i)' % (evt.reason, evt.code)
            if (not flexx.is_notebook) and (not self.nodejs):
                document.body.innerHTML = msg
            else:
                console.info(msg)
        def on_ws_error(self, evt):
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
            flexx.ws.send("PRINT " + msg)
            console.ori_log(msg)
        def info(self, msg):
            flexx.ws.send("INFO " + msg)
            console.ori_info(msg)
        def warn(self, msg):
            flexx.ws.send("WARN " + msg)
            console.ori_warn(msg)
        def error(self, msg):
            flexx.ws.send("ERROR " + msg)
            console.ori_error(msg)
        def on_error(self, evt):
            msg = evt
            if evt.message and evt.lineno:  # message, url, linenumber (not in nodejs)
                msg = "On line %i in %s:\n%s" % (evt.lineno, evt.filename, evt.message)
            elif evt.stack:
                msg = evt.stack
            flexx.ws.send("ERROR " + msg)
        
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
            console.warn('Invalid command: ' + msg)
    
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
    * dynamic: all of the Mirrored classes will be defined dynamically.
      Note that this makes debugging difficult. Mainly intended for
      testing purposes.
    
    Note that any Mirrored classes defined once the first connects
    will be dynamically defined, regardless of the chosen mode (after
    all, the page will already have been served).
    
    Note that not all delivery methods support all modes.
    
    """
    
    _instance = None
    
    def __init__(self):
        
        # Enforce singleton
        if ClientCode._instance is not None:
            raise RuntimeError('ClientCode must be singleton')
        ClientCode._instance = self
        
        self._files = OrderedDict()
        self._cache = {}
        
        self._preloaded_mirrored_classes = set()
        
        # Init dicts for JS and CSS code. The index represents the name
        # of the .js or .css file, or starts with "index-" in which
        # case the code should be in the main page.
        self._js = OrderedDict()
        self._css = OrderedDict()
        
        # Init flexx core code
        self._js['flexx'] = []
        self._css['flexx'] = []
        self._js['flexx'].append(FlexxJS.jscode)
        self._js['flexx'].append('var flexx = new FlexxJS();\n')
    
    @property
    def mode(self):
        """ Get the mode to serve JS/CSS code: 'split', 'single', or 'dynamic'.
        """
        return os.getenv('FLEXX_SERVE_MODE', 'split')
    
    def _collect(self):
        """ The first time this is called, all existing Mirrored classes
        are collected, and their JS and CSS extracted. Any further calls
        to this method have no effect. This method is called upon app
        creation.
        
        The collected JS and CSS will be served via HTML; any Mirrored
        classes that are used later on will be dynamically defined (i.e.
        injected) via the websocket interface.
        """
        if self._preloaded_mirrored_classes:
            return
        if self.mode == 'dynamic':
            return
        
        # todo: Maybe at some point we may want to include external js files?
        # # Determine JS files
        # for fname in ['serialize.js', #'main.js', #'layouts.js',
        #              ]:# 'phosphor-core.min.js', 'phosphor-ui.min.js']:
        #     if fname.startswith('phosphor'):
        #         self._files[fname] = os.path.join(HTML_DIR, 'phosphor', fname)
        #     else:
        #         self._files[fname] = os.path.join(HTML_DIR, fname)
        # 
        # # Determine CSS files
        # for fname in []:#['main.css', 'layouts.css', ]:#'phosphor-ui.min.css']:
        #     if fname.startswith('phosphor'):
        #         self._files[fname] = os.path.join(HTML_DIR, 'phosphor', fname)
        #     else:
        #         self._files[fname] = os.path.join(HTML_DIR, fname)
        
        # Collect JS from mirrored classes
        #from .mirrored import get_mirrored_classes
        from .paired import get_mirrored_classes
        
        self._js['flexx-ui'] = []
        self._js['index-other'] = []
        self._css['flexx-ui'] = []
        self._css['index-other'] = []
        
        for cls in get_mirrored_classes():
            self._preloaded_mirrored_classes.add(cls)
            if cls.__module__.startswith('flexx.app'):
                key = 'flexx'
            elif cls.__module__.startswith('flexx.ui'):
                key = 'flexx-ui'
            else:
                key = 'index-other'
            self._js[key].append(cls.JS.CODE)
            self._css[key].append(cls.CSS)  # the CSS is '' if not specified for that class
    
    def get_defined_mirrored_classes(self):
        """ Get a list of all mirrored classes that will be defined
        by serving the JS/CSS code. Returns an empty list when in 
        'dynamic' mode.
        """
        self._collect()
        if self.mode == 'dynamic':
            return []
        else:
            return self._preloaded_mirrored_classes
    
    def load(self, fname):
        """ Get the source of the given file as a string.
        """
        if fname.endswith('.js') and fname[:-3] in self._js:
            return self.get_js(fname[:-3])
        elif fname.endswith('.css') and fname[:-4] in self._css:
            return self.get_css(fname[:-4])
        elif fname not in self._files:
            raise IOError('Invalid source file')
        elif fname in self._cache:
            return self._cache[fname]
        else:
            filename = self._files[fname]
            src = open(filename, 'rt').read()
            #self._cache[fname] = src  # caching disabled for easer dev
            return src
    
    def get_js(self, selection='all'):
        """ Get JavaScript as a single string.
        """
        self._collect()
        parts = ['"use strict";']
        if selection == 'all':
            for key in self._js:
                parts.extend(self._js[key])
        else:
            parts.extend(self._js[selection])
        return '\n\n'.join(parts)
    
    def get_css(self, selection='all'):
        """ Get CSS as a single string.
        """
        self._collect()
        parts = []
        if selection == 'all':
            for key in self._css:
                parts.extend(self._css[key])
        else:
            parts.extend(self._css[selection])
        return '\n\n'.join(parts)
    
    def get_page(self):
        """ Get the string for an HTML page that can show a Flexx app.
        """
        return self._get_page(self.mode)
    
    def get_page_for_export(self, commands):
        """ Get the string for a single exported HTML page.
        """
        # Create lines to init app
        lines = []
        lines.append('flexx.is_exported = true;\n')
        lines.append('flexx.runExportedApp = function () {')
        lines.extend(['    flexx.command(%r);' % c for c in commands])
        lines.append('};\n')
        
        # Create a temporary extra element
        self._js['index-export'] = ['\n'.join(lines)]
        try:
            return self._get_page('single')  # todo: or split, depending on export mode
        finally:
            self._js.pop('index-export')
    
    def _get_page(self, mode):
        """ This code takes the template, the collected JS and CSS and
        composes an index page to serve/export.
        """
        assert mode in ('split', 'single', 'dynamic')
        
        # Init source code from template
        js_elements = []
        css_elements = []
        
        # Get JS DOM elements
        for key in self._js:
            code = self.get_js(key)
            if not code.strip():
                continue
            js = ''
            if ((mode == 'single') or 
                (mode == 'split' and key.startswith('index')) or 
                (mode == 'dynamic' and key == 'flexx')):
                js = "<script>\n/* JS for %s */\n%s\n</script>" % (key, code)
            elif mode == 'split':
                js = "<script src='%s.js'></script>" % key
            js_elements.append(js)
        
        # Get CSS DOM elements
        for key in self._css:
            code = self.get_css(key)
            if not code.strip():
                continue
            css = ''
            if ((mode == 'single') or 
                (mode == 'split' and key.startswith('index')) or 
                (mode == 'dynamic' and key == 'flexx')):
                css = "<style>\n/* CSS for %s */\n%s\n</style>" % (key, code)
            elif mode == 'split':
                css = "<link rel='stylesheet' type='text/css' href='%s.css' />" % key
            css_elements.append(css)
        
        # Compose index page
        src = INDEX
        src = src.replace('JS-HOOK', '\n\n'.join(js_elements))
        src = src.replace('CSS-HOOK', '\n\n'.join(css_elements))
        
        return src


# Create the one instance of this class. We cannot have one object
# per app, since serve.py needs get_page() before there is an app.
clientCode = ClientCode()


class Exporter(object):
    """ Object that can be used by an app inplace of the websocket to
    export apps to standalone HTML. The object tracks the commands send
    by the app, so that these can be re-played in the exported document.
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
        """ Write html document to the given file.
        """
        # todo: allow writing in split mode
        html = self.to_html()
        open(filename, 'wt').write(html)
        print('Exported app to %r' % filename)
    
    def to_html(self):
        """ Get the HTML string.
        """
        return clientCode.get_page_for_export(self._commands)
    

def minify(code):
    """ Very minimal JS minification algorithm. Can probably be better.
    May contain bugs. Only operates well on JS without syntax errors.
    """
    space_safe = ' =+-/*&|(){},.><:;'
    chars = ['\n']
    class non_local: pass
    non_local._i = -1
    
    def read():
        non_local._i += 1
        if non_local._i < len(code):
            return code[non_local._i]
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
