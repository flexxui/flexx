"""
The client's core Flexx engine, implemented in PyScript.
"""

from ..pyscript import py2js
from ..pyscript.stubs import (undefined, window, root, console, document,
                             module, flexx, require, typeof)


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
        loc = window.location
        self.ws_url = ('ws://%s:%s/%s/ws' % (loc.hostname, loc.port, loc.pathname))
        self.is_exported = False
        self.classes = {}
        self.instances = {}
        if typeof(window) is 'undefined' and typeof(module) is 'object':
            # nodejs (call exit on exit and ctrl-c
            self._global = root
            self.nodejs = True
            root.setTimeout(self.init, 1)  # ms
            root.process.on('exit', self.exit, False)
            root.process.on('SIGINT', self.exit, False)
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
            print('Flexx: hey, I am in an exported notebook!')
        else:
            flexx.initSocket()
            flexx.initLogging()
        
    def exit(self):
        """ Called when runtime is about to quit. """
        if self.ws:  # is not null or undefined
            self.ws.close()
            self.ws = None
    
    def get(self, id):
        """ Get instance of a Model class.
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
            ws.send('hiflexx ' + window.flexx_session_id)
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
            ws.onerror = on_ws_error
    
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
            if flexx.ws is not None:
                flexx.ws.send("PRINT " + msg)
        def info(self, msg):
            console.ori_info(msg)
            if flexx.ws is not None:
                flexx.ws.send("INFO " + msg)
        def warn(self, msg):
            console.ori_warn(msg)
            if flexx.ws is not None:
                flexx.ws.send("WARN " + msg)
        def error(self, msg):
            console.ori_error(msg)
            if flexx.ws is not None:
                flexx.ws.send("ERROR " + msg)
        def on_error(self, evt):
            msg = evt
            if evt.message and evt.lineno:  # message, url, linenumber (not in nodejs)
                msg = "On line %i in %s:\n%s" % (evt.lineno, evt.filename, evt.message)
            elif evt.stack:
                msg = evt.stack
            if flexx.ws is not None:
                flexx.ws.send("ERROR " + msg)
        
        # Set new versions
        console.log = log
        console.info = info
        console.warn = warn
        console.error = error
        # Create error handler, so that JS errors get into Python
        if self.nodejs:
            root.process.on('uncaughtException', on_error, False)
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
        if (data.length >= 3 &&
            data[0] === 0xef && data[1] === 0xbb && data[2] === 0xbf) {
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
                result += String.fromCharCode(((c & 15) << 12) |
                                              ((c2 & 63) << 6) | (c3 & 63));
                i += 3;
            }
        }
        return result;
        """
