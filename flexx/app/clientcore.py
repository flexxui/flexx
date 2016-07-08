"""
The client's core Flexx engine, implemented in PyScript.
"""

from ..pyscript import py2js, undefined, window

flexx_session_id = location = require = module = typeof = None  # fool PyFlakes


@py2js(inline_stdlib=False)
class FlexxJS:
    """ JavaScript Flexx module. This provides the connection between
    the Python and JS (via a websocket).
    """
    
    def __init__(self):
        
        self.ws = None
        self.last_msg = None
        self.is_notebook = False  # if not, we "close" when the ws closes
        # For nodejs, the location is set by the flexx nodejs runtime.
        address = location.hostname
        if location.port:
            address += ':' + location.port
        if location.pathname:
            address += '/' + location.pathname
        self.ws_url = 'ws://%s/ws' % address
        self.is_exported = False
        self.classes = {}
        self.instances = {}
        if typeof(window) is 'undefined' and typeof(module) is 'object':
            # nodejs (call exit on exit and ctrl-c
            self._set_window_as_global()  # create alias
            self.nodejs = True
            window.setTimeout(self.init, 1)  # ms
            window.process.on('exit', self.exit, False)
            window.process.on('SIGINT', self.exit, False)
            window.setTimeout(self.exit, 10000000)  # keep alive ~35k years
        else:
            # browser
            window.addEventListener('load', self.init, False)
            window.addEventListener('beforeunload', self.exit, False)
        window.flexx = self
    
    def _set_window_as_global(self):  # https://github.com/nodejs/node/pull/1838
        """ global.window = global;
        """
    
    def init(self):
        """ Called after document is loaded. """
        if window.flexx.is_exported:
            window.flexx.runExportedApp()
        elif window.flexx.is_notebook and not (window.IPython and 
                                               window.IPython.notebook and 
                                               window.IPython.notebook.session):
            print('Flexx: hey, I am in an exported notebook!')
        else:
            window.flexx.initSocket()
            window.flexx.initLogging()
        
    def exit(self):
        """ Called when runtime is about to quit. """
        if self.ws:  # is not null or undefined
            self.ws.close()
            self.ws = None
    
    def get(self, id):
        """ Get instance of a Model class.
        """
        if id == 'body':
            return window.document.body
        else:
            return self.instances[id]
    
    def initSocket(self):
        """ Make the connection to Python.
        """
        
        # Check WebSocket support
        if self.nodejs:
            try:
                WebSocket = require('ws')
            except Exception:
                # Better error message
                raise "FAIL: you need to 'npm install -g ws' (or 'websocket')."
        else:
            WebSocket = window.WebSocket
            if (WebSocket is undefined):
                window.document.body.innerHTML = 'Browser does not support WebSockets'
                raise "FAIL: need websocket"
        # Open web socket in binary mode
        self.ws = ws = WebSocket(window.flexx.ws_url)
        #ws.binaryType = "arraybuffer"  # would need utf-decoding -> slow
        
        def on_ws_open(evt):
            window.console.info('Socket connected')
            ws.send('hiflexx ' + flexx_session_id)
        def on_ws_message(evt):
            window.flexx.last_msg = msg = evt.data or evt
            #msg = window.flexx.decodeUtf8(msg)
            window.flexx.command(msg)
        def on_ws_close(evt):
            self.ws = None
            msg = 'Lost connection with server'
            if evt and evt.reason:  # nodejs-ws does not have it?
                msg += ': %s (%i)' % (evt.reason, evt.code)
            if (not window.flexx.is_notebook) and (not self.nodejs):
                window.document.body.innerHTML = msg
            else:
                window.console.info(msg)
        def on_ws_error(self, evt):
            self.ws = None
            window.console.error('Socket error')
        
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
        if window.console.ori_log:
            return  # already initialized the loggers
        # Keep originals
        window.console.ori_log = window.console.log
        window.console.ori_info = window.console.info or window.console.log
        window.console.ori_warn = window.console.warn or window.console.log
        window.console.ori_error = window.console.error or window.console.log
        
        def log(self, msg):
            window.console.ori_log(msg)
            if window.flexx.ws is not None:
                window.flexx.ws.send("PRINT " + msg)
        def info(self, msg):
            window.console.ori_info(msg)
            if window.flexx.ws is not None:
                window.flexx.ws.send("INFO " + msg)
        def warn(self, msg):
            window.console.ori_warn(msg)
            if window.flexx.ws is not None:
                window.flexx.ws.send("WARN " + msg)
        def error(self, msg):
            window.console.ori_error(msg)
            if window.flexx.ws is not None:
                window.flexx.ws.send("ERROR " + msg)
        def on_error(self, evt):
            msg = evt.message
            if evt.error.stack:
                stack = [x.replace('@', ' @ ') if '.js' in x else x.split('@')[0]
                         for x in evt.error.stack.splitlines()]
                msg += '\n' + '\n'.join(stack)
            elif evt.message and evt.lineno:  # message, url, linenumber (not in nodejs)
                msg += "\nIn %s:%i" % (evt.filename, evt.lineno)
            window.console.error(msg)
            evt.preventDefault()  # Don't do the standard error 
        # Set new versions
        window.console.log = log
        window.console.info = info
        window.console.warn = warn
        window.console.error = error
        # Create error handler, so that JS errors get into Python
        if self.nodejs:
            window.process.on('uncaughtException', on_error, False)
        else:
            window.addEventListener('error', on_error, False)
    
    def command(self, msg):
        """ Execute a command received from the server.
        """
        if msg.startswith('PRINT '):
            window.console.ori_log(msg[6:])
        elif msg.startswith('EVAL '):
            window._ = eval(msg[5:])
            window.flexx.ws.send('RET ' + window._)  # send back result
        elif msg.startswith('EXEC '):
            eval(msg[5:])  # like eval, but do not return result
        elif msg.startswith('DEFINE-JS '):
            if self.nodejs:
                eval(msg[10:])  # best we can do
            else:
                el = window.document.createElement("script")
                el.innerHTML = msg[10:]
                window.document.body.appendChild(el)
        elif msg.startswith('DEFINE-CSS '):
            # http://stackoverflow.com/a/707580/2271927
            el = window.document.createElement("style")
            el.type = "text/css"
            el.innerHTML = msg[11:]
            window.document.body.appendChild(el)
        elif msg.startswith('TITLE '):
            if not self.nodejs:
                window.document.title = msg[6:]
        elif msg.startswith('ICON '):
            if not self.nodejs:
                link = window.document.createElement('link')
                link.rel = 'icon'
                link.href = msg[5:]
                window.document.head.appendChild(link)
                #window.document.getElementsByTagName('head')[0].appendChild(link);
        elif msg.startswith('OPEN '):
            window.win1 = window.open(msg[5:], 'new', 'chrome')
        else:
            window.console.warn('Invalid command: "' + msg + '"')
    
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
