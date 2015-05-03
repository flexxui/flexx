"""
This module defined the client PyScript code to handle the connection
with the Python server.

Further, it defines a (singleton) class that can collects all the
JS/CSS, and provides this client code (HTML/JS/CSS) in diffent ways.
This streamlines the inclusion in Jupyter and our export mechanism.
"""

import os
from collections import OrderedDict
from ..pyscript import js

# todo: minification


THIS_DIR = os.path.abspath(os.path.dirname(__file__))
HTML_DIR = os.path.join(os.path.dirname(THIS_DIR), 'html')

INDEX = """
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>Flexx UI</title>

<style>
"use strict""

CSS-HERE
</style>

<script>
"use strict";

JS-HERE
</script>

</head>

<body id='body'>
    
    <div id="log" style="display: none;"> LOG:<br><br></div>

</body>
</html>
"""


@js
class FlexxJS:
    """ JavaScript Flexx module.
    """
    
    def __init__(self):
        """ Bootstrap Flexx. """
        
        self.ws = None
        self.last_msg = None
        self.is_full_page = True
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
        else:
            flexx.initSocket()
            flexx.initLogging()
        
    def exit(self):
        """ Called when runtime is about to quit. """
        if self.ws:  # is not null or undefined
            self.ws.close()
            self.ws = None
    
    def get(self, id):
        """ Get instance
        """
        if id == 'body':
            return document.body
        else:
            return self.instances[id]
    
    def initSocket(self):
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
            if flexx.is_full_page and not self.nodejs:
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
        if console.ori_log:
            return  # already initialized the loggers
        # Keep originals
        console.ori_log = console.log
        console.ori_info = console.info or console.log
        console.ori_warn = console.warn or console.log
        
        def log(self, msg):
            flexx.ws.send("PRINT " + msg)
            console.ori_log(msg)
        def info(self, msg):
            flexx.ws.send("INFO " + msg)
            console.ori_info(msg)
        def warn(self, msg):
            flexx.ws.send("WARN " + msg)
            console.ori_warn(msg)
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


class GlobalClientCode(object):
    """
    """
    
    def __init__(self):
        
        self._files = OrderedDict()
        self._cache = {}
        
        self._js_codes = []
        self._css_codes = []
    
    @classmethod
    def collect(self):
        if self._global_js_codes:
            return
        
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
        from .mirrored import get_mirrored_classes
        # self._mirrored_js, self._mirrored_css = [], []
        # todo: try not collecting, it should still work; all func provided via socket
        for cls in get_mirrored_classes():
            #self._mirrored_js.append(cls.get_js())
            #self._mirrored_css.append(cls.get_css())
            #self._global_js_codes.append(cls)
            self._global_css_codes.append(cls.get_css())

    def load(self, fname):
        """ Get the source of the given file as a string.
        """
        if fname not in self._files:
            raise IOError('Invalid source file')
        elif fname in self._cache:
            return self._cache[fname]
        else:
            filename = self._files[fname]
            src = open(filename, 'rt').read()
            #self._cache[fname] = src  # caching disabled for easer dev
            return src
    
    def get_js(self):
        """ Get all JavaScript as a single string.
        """
        parts = []
        parts.append('/* ===== Flexx module ===== */')
        parts.append(FlexxJS.jscode)
        parts.append('var flexx = new FlexxJS();\n')
        # # Files
        # for fname in self._files:
        #     if fname.endswith('.js'):
        #         parts.append('/* ===== %s ===== */' % fname)
        #         parts.append(self.load(fname))
        # Mirrored code
        parts.append('/* ===== mirrored classes ===== */')
        for cls in self._js_codes:
            parts.append(cls.get_js())
            self._known_codes.add(cls.get_jshash())
        return '\n\n'.join(parts)
    
    def get_css(self):
        """ Get all CSS packed in a single <style> tag.
        """
        parts = []
        # for fname in self._files:
        #     if fname.endswith('.css'):
        #         parts.append('/* ===== %s ===== */' % fname)
        #         parts.append(self.load(fname))
        # Mirrored code
        parts.append('/* ===== Python-defined CSS ===== */')
        for src in self._css_codes:
            parts.append(src)
        return '\n\n'.join(parts)
    
    def get_page(self):
        """ Get the string for a single HTML page that can show a Flexx app.
        """
        src = INDEX
        src = src.replace('CSS-HERE', self.get_css())
        src = src.replace('JS-HERE', self.get_js())
        return src
    
    def get_page_light(self):
        """ Get a page that relies on external flexx.js and flexx.css.
        """
        raise NotImplementedError()
    
    def build(self, dirname):
        """ Create the flexx js library and css file. Place in the given dir.
        """
        assert os.path.isdir(dirname)
        with open(os.path.join(dirname, 'flexx.js')) as f:
            f.write(self.get_js())
        with open(os.path.join(dirname, 'flexx.css')) as f:
            f.write(self.get_css())


# class ClientCode(object):
#     """ Collect code that the client needs and provide a few ways to
#     get the code to the client.
#     """
#     
#     def __init__(self):
#         
#         self._in_nb = False
#         
#         self.collect()  # happens only once
#         
#         self._known_codes = set()
#         for cls in globalClientCode._js_codes:
#             self._known_codes.add(cls)
#     
#     def add_code(self, mirrored_class):
#         if not (isinstance(mirrored_class, type) and hasattr(mirrored_class, 'get_js') and hasattr(mirrored_class, 'get_jshash')):
#             raise ValueError('Not a Mirrored class')
#         if mirrored_class.get_jshas() not in self._known_codes:
#             self._js_codes.append(mirrored_class)
#     
#     
#     def export(self, filename):
#         """ Export the current app to a single HTML page.
#         """
#         # todo: needs commands
#         with open(filename, 'wt') as f:
#             f.write(self.get_page())
#     
#     def export_light(self, filename):
#         """ Get a page that relies on external flexx.js and flexx.css.
#         """
#         raise NotImplementedError()


clientCode = GlobalClientCode()
