"""
The client's core Flexx engine, implemented in PyScript.
"""

from ..pyscript import this_is_js, RawJS
from ..pyscript.stubs import window, undefined, time

# This module gets transpiled to JavaScript as a whole
__pyscript__ = True


class Flexx:
    """ JavaScript Flexx module. This provides the connection between
    the Python and JS (via a websocket).
    """
    
    def __init__(self):
        # Init (overloadable) variables. These can be set by creating
        # a window.flexx object *before* instantiating this class, or by
        # setting them on this object before the init() is called.
        self.is_notebook = False
        self.is_exported = False
        
        # Copy attributes from temporary flexx object
        if window.flexx.init:
            raise RuntimeError('Should not create global Flexx object more than once.')
        for key in window.flexx.keys():
            self[key] = window.flexx[key]  # session_id, app_name, and maybe more
        
        # Keep track of sessions
        self._session_count = 0
        self.sessions = {}
        
        # Note: flexx.init() is not auto-called when Flexx is embedded
        window.addEventListener('load', self.init, False)
        window.addEventListener('unload', self.exit, False)  # not beforeunload
    
    def init(self):
        """ Called after document is loaded. """
        # Create div to put dynamic CSS assets in
        self._asset_node = window.document.createElement("div")
        self._asset_node.id = 'Flexx asset container'
        window.document.body.appendChild(self._asset_node)
        
        if self.is_exported:
            if self.is_notebook:
                print('Flexx: I am in an exported notebook!')
            else:
                print('Flexx: I am in an exported app!')
                self.runExportedApp()
        else:
            print('Flexx: Initializing')
            if not self.is_notebook:
                self._remove_querystring()
            self.initLogging()
    
    def _remove_querystring(self):
        # remove querystring ?session=x
        try:
            window.history.replaceState(window.history.state, '',
                                        window.location.pathname)
        except Exception:
            pass  # e.g. firefox-app/nw
    
    def exit(self):
        """ Called when runtime is about to quit. """
        for session in self.sessions.values():
            session.exit()
    
    def spin(self, text='*'):
        RawJS("""
        if (!window.document.body) {return;}
        var el = window.document.body.children[0];
        if (el && el.classList.contains("flx-spinner")) {
            if (text === null) {
                el.style.display = 'none';  // Stop the spinner
            } else {
                el.children[0].innerHTML += text.replace(/\*/g, '&#9632');
            }
        }
        """)
    
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
        
        def log(msg):
            window.console.ori_log(msg)
            for session in self.sessions.values():
                session.send_command("PRINT", str(msg))
        def info(msg):
            window.console.ori_info(msg)
            for session in self.sessions.values():
                session.send_command("INFO", str(msg))
        def warn(msg):
            window.console.ori_warn(msg)
            for session in self.sessions.values():
                session.send_command("WARN", str(msg))
        def error(msg):
            evt = dict(message=str(msg), error=msg, preventDefault=lambda: None)
            on_error(evt)
        def on_error(evt):
            msg = evt.message
            if evt.error and evt.error.stack:  # evt.error can be None for syntax err
                stack = evt.error.stack.splitlines()
                if evt.message in stack[0]:
                    stack.pop(0)
                msg += '\n' + '\n'.join(stack)
                session_needle = '?session_id=' + self.id
                msg = msg.replace('@', ' @ ').replace(session_needle, '')  # Firefox
            elif evt.message and evt.lineno:  # message, url, linenumber
                msg += "\nIn %s:%i" % (evt.filename, evt.lineno)
            # Handle error
            evt.preventDefault()  # Don't do the standard error 
            window.console.ori_error(msg)
            for session in self.sessions.values():
                session.send_command("ERROR", evt.message)
        on_error = on_error.bind(self)
        # Set new versions
        window.console.log = log
        window.console.info = info
        window.console.warn = warn
        window.console.error = error
        # Create error handler, so that JS errors get into Python
        window.addEventListener('error', on_error, False)
    
    def create_session(self, app_name, session_id, ws_url):
        # todo: should this be delayed if we did not call init yet?
        s = JsSession(app_name, session_id, ws_url)
        self._session_count += 1
        self['s' + self._session_count] = s
        self.sessions[session_id] = s


class JsSession:
    
    def __init__(self, app_name, id, ws_url=None):
        self.app_name = app_name
        self.id = id
        self.ws_url = ws_url
        
        # Maybe this is JLab
        if not self.id:
            jconfig = window.document.getElementById('jupyter-config-data')
            if jconfig:
                try:
                    config = JSON.parse(jconfig.innerText)
                    self.id = config.flexx_session_id
                    self.app_name = config.flexx_app_name
                except Exception as err:
                    print(err)
        
        # Init internal variables
        self._init_time = time()
        self._pending_commands = []  # to pend raw commands during init
        self._asset_count = 0
        self._ws = None
        self.last_msg = None
        # self.classes = {}
        self.instances = {}
        
        self.initSocket()
    
    def exit(self):
        if self._ws:  # is not null or undefined
            self._ws.close()
            self._ws = None
            # flexx.instances.sessions.pop(self)  might be good, but perhaps not that much neede?
    
    def send_command(self, *command):
        if self._ws is not None:
            try:
                bb = serializer.encode(command)
            except Exception as err:
                print('Command that failed to encode:')
                print(command)
                raise err
            self._ws.send(bb)
    
    def instantiate_component(self, module, cname, id, args, kwargs):
        # Maybe we still have the instance?
        c = self.instances.get(id, None)
        if c is not None and c._disposed is False:
            return c
        # Find the class
        m = flexx.require(module)
        Cls = m[cname]  # noqa
        # Instantiate
        kwargs['flx_session'] = self
        kwargs['flx_id'] = id
        c = Cls(*args, **kwargs)
        return c
    
    def _register_component(self, c):
        self.instances[c._id] = c
    
    # todo: do we need a global version?
    def get_instance(self, id):
        """ Get instance of a Component class, or None. Or the document body
        if "body" is given.
        """
        if id == 'body':
            return window.document.body
        else:
            return self.instances.get(id, None)
    
    def dispose_object(self, id):
        """ Dispose the object with the given id.
        """
        ob = self.instances[id]
        if ob is not undefined:
            ob.dispose()  # Model.dispose() removes itself from flexx.instances
    
    def initSocket(self):
        """ Make the connection to Python.
        """
        # Check WebSocket support
        WebSocket = window.WebSocket
        if (WebSocket is undefined):
            window.document.body.innerHTML = 'Browser does not support WebSockets'
            raise "FAIL: need websocket"
        
        # Construct ws url
        if not self.ws_url:
            proto = 'ws'
            if window.location.protocol == 'https:':
                proto = 'wss'
            address = window.location.hostname
            if window.location.port:
                address += ':' + window.location.port
            self.ws_url = '%s://%s/flexx/ws/%s' % (proto, address, self.app_name)
        # Resolve public hostname
        self.ws_url = self.ws_url.replace('0.0.0.0', window.location.hostname)
        # Open web socket in binary mode
        self._ws = ws = WebSocket(self.ws_url)
        ws.binaryType = "arraybuffer"
        
        def on_ws_open(evt):
            window.console.info('Socket opened with session id ' + self.id)
            self.send_command('HI_FLEXX', self.id)
        def on_ws_message(evt):
            msg = evt.data or evt  # bsdf-encoded command
            if self._pending_commands is None:
                # Direct mode
                self._receive_raw_command(msg)
            else:
                # Indirect mode, to give browser draw-time during loading
                if len(self._pending_commands) == 0:
                    window.setTimeout(self._process_commands, 0)
                self._pending_commands.push(msg)
        def on_ws_close(evt):
            self._ws = None
            msg = 'Lost connection with server'
            if evt and evt.reason:
                msg += ': %s (%i)' % (evt.reason, evt.code)
            if not self.is_notebook:
                # todo: show modal or cooky-like dialog instead of killing whole page
                window.document.body.innerHTML = msg
            else:
                window.console.info(msg)
        def on_ws_error(self, evt):
            self._ws = None
            window.console.error('Socket error')
        
        # Connect
        ws.onopen = on_ws_open
        ws.onmessage = on_ws_message
        ws.onclose = on_ws_close
        ws.onerror = on_ws_error
    
    def _process_commands(self):
        """ A less direct way to process commands, which gives the
        browser time to draw about every other JS asset. This is a
        tradeoff between a smooth spinner and fast load time.
        """
        while self._pending_commands is not None and len(self._pending_commands) > 0:
            msg = self._pending_commands.pop(0)
            try:
                command = self._receive_raw_command(msg)
            except Exception as err:
                window.setTimeout(self._process_commands, 0)
                raise err
            if command[0] == 'DEFINE':
                self._asset_count += 1
                if (self._asset_count % 3) == 0:
                    if len(self._pending_commands):
                        window.setTimeout(self._process_commands, 0)
                    break
    
    def _receive_raw_command(self, msg):
        return self._receive_command( serializer.decode(msg))
    
    def _receive_command(self, command):
        """ Process a command send from the server.
        """
        cmd = command[0]
        if cmd == 'PING':
            self.send_command('PONG', command[1])
        elif cmd == 'INIT_DONE':
            window.flexx.spin(None)
            while len(self._pending_commands):
                self._receive_raw_command(self._pending_commands.pop(0))
            self._pending_commands = None
            # print('init took', time() - self._init_time)
        elif cmd == 'PRINT':
            window.console.ori_log(command[1])
        elif cmd == 'EVAL':
            x = None
            if len(command) == 2:
                x = eval(command[1])
            elif len(command) == 3:
                x = eval('this.instances.' + command[1] + '.' + command[2])
            console.log(str(x))  # print and sends back result
        # elif cmd == 'EXEC':
        #     eval(command[1])  # like eval, but do not return result
        elif cmd == 'INVOKE':
            id, name, args = command[1:]
            ob = self.instances.get(id, None)
            if ob is not None:
                ob[name](*args)
        elif cmd == 'INSTANTIATE':
            self.instantiate_component(*command[1:])  # module, cname, id, args, kwargs
        elif cmd == 'DEFINE':
            #and command[1] == 'JS' or command[1] == 'DEFINE-JS-EVAL '):
            kind, name, code = command[1:]
            window.flexx.spin()
            address = window.location.protocol + '//' + self.ws_url.split('/')[2]
            code += '\n/*# sourceURL=%s/flexx/assets/shared/%s*/\n' % (address, name)
            if kind == 'JS-EVAL':
                eval(code)
            elif kind == 'JS':
                # With this method, sourceURL does not work on Firefox,
                # but eval might not work for assets that don't "use strict"
                # (e.g. Bokeh). Note, btw, that creating links to assets does
                # not work because these won't be loaded on time.
                el = window.document.createElement("script")
                el.id = name
                el.innerHTML = code
                self._asset_node.appendChild(el)
            elif kind == 'CSS':
                el = window.document.createElement("style")
                el.type = "text/css"
                el.id = name
                el.innerHTML = code
                self._asset_node.appendChild(el)
            else:
                window.console.error('Dont know how to DEFINE ' +
                                     name + ' with "' + kind + '".')
        elif cmd == 'TITLE':
            window.document.title = command[1]
        elif cmd == 'ICON':
            link = window.document.createElement('link')
            link.rel = 'icon'
            link.href = command[1]
            window.document.head.appendChild(link)
            #window.document.getElementsByTagName('head')[0].appendChild(link);
        elif cmd == 'OPEN':
            window.win1 = window.open(command[1], 'new', 'chrome')
        else:
            window.console.error('Invalid command: "' + cmd + '"')
        return command

# todo: in bsdf there is utf8 encode/decode code, check which is better, put that in bsdf, and use it here
def decodeUtf8(arrayBuffer):
    RawJS("""
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
    """)
    return RawJS("result")


# In Python, we need some extras for the serializer to work
if this_is_js():
    bsdf = RawJS("flexx.require('bsdf')")
    serializer = bsdf.BsdfSerializer()
else:
    # Include bsdf.js
    # todo: use vendored bsdf.py and on-line version of bsdf.js
    import bsdf
    serializer = bsdf.BsdfSerializer()
    serializer.__module__ = __name__



# 
# class Serializer:
#     
#     def __init__(self):
#         self._revivers = _revivers = {}
#     
#         def loads(text):
#             return JSON.parse(text, _reviver)
#         
#         def saves(obj):
#             try:
#                 res = JSON.stringify(obj, _replacer)
#                 if res is undefined:
#                     raise TypeError()
#                 return res
#             except TypeError:
#                 raise TypeError('Cannot serialize object to JSON: %r' % obj)
#         
#         def add_reviver(type_name, func):
#             assert isinstance(type_name, str)
#             _revivers[type_name] = func
#         
#         def _reviver(dct, val=undefined):
#             if val is not undefined:  # pragma: no cover
#                 dct = val
#             if isinstance(dct, dict):
#                 type = dct.get('__type__', None)
#                 if type is not None:
#                     func = _revivers.get(type, None)
#                     if func is not None:
#                         return func(dct)
#             return dct
#         
#         def _replacer(obj, val=undefined):
#             if val is undefined:  # Py
#                 
#                 try:
#                     return obj.__json__()  # same as in Pyramid
#                 except AttributeError:
#                     raise TypeError('Cannot serialize object to JSON: %r' % obj)
#             else:  # JS - pragma: no cover
#                 if (val is not None) and val.__json__ is not undefined:
#                     return val.__json__()
#                 return val
#         
#         self.loads = loads
#         self.saves = saves
#         self.add_reviver = add_reviver


## Instantiate


# serializer = Serializer()

if this_is_js():
    window.flexx = Flexx()
    window.flexx.serializer = serializer
