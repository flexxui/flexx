"""
The client's core Flexx engine, implemented in PyScript.
"""

from ..pyscript import this_is_js, RawJS
from ..pyscript.stubs import window, undefined, time, console, JSON

# This module gets transpiled to JavaScript as a whole
__pyscript__ = True


class Flexx:
    """ JavaScript Flexx module. This provides the connection between
    the Python and JS (via a websocket).
    """
    
    def __init__(self):
        
        if window.flexx.init:
            raise RuntimeError('Should not create global Flexx object more than once.')
        
        # Init (overloadable) variables. These can be set by creating
        # a window.flexx object *before* instantiating this class, or by
        # setting them on this object before the init() is called.
        self.is_notebook = False
        self.is_exported = False
        
        # Copy attributes from temporary object (e.g. is_notebook, require, ...)
        for key in window.flexx.keys():
            self[key] = window.flexx[key]
        
        # We need a global main widget (shared between sessions)
        self.need_main_widget = True  # Used/set in ui/_widget.py
        
        # Keep track of sessions
        self._session_count = 0
        self.sessions = {}
        
        # Note: flexx.init() is not auto-called when Flexx is embedded
        window.addEventListener('load', self.init, False)
        window.addEventListener('unload', self.exit, False)  # not beforeunload
    
    def init(self):
        """ Called after document is loaded. """
        # Create div to put dynamic CSS assets in
        self.asset_node = window.document.createElement("div")
        self.asset_node.id = 'Flexx asset container'
        window.document.body.appendChild(self.asset_node)
        
        if self.is_exported:
            if self.is_notebook:
                print('Flexx: I am in an exported notebook!')
            else:
                print('Flexx: I am in an exported app!')
                self.run_exported_app()
        else:
            print('Flexx: Initializing')
            if not self.is_notebook:
                self._remove_querystring()
            self.init_logging()
    
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
    
    def init_logging(self):
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
        # The call to this method is embedded by get_page(),
        # or injected by init_notebook().
        # Can be called before init() is called.
        s = JsSession(app_name, session_id, ws_url)
        self._session_count += 1
        self['s' + self._session_count] = s
        self.sessions[session_id] = s


class JsSession:
    
    def __init__(self, app_name, id, ws_url=None):
        self.app = None  # the root component (can be a PyComponent)
        self.app_name = app_name
        self.id = id
        self.status = 1
        self.ws_url = ws_url
        self._component_counter = 0
        self._disposed_ob = {'_disposed': True}
        
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
        self.instances_to_check_size = {}
        
        if not window.flexx.is_exported:
            self.init_socket()
        
        # Initiate service to track resize
        window.addEventListener('resize', self._check_size_of_objects, False)
        window.setInterval(self._check_size_of_objects, 1000)
    
    def exit(self):
        if self._ws:  # is not null or undefined
            self._ws.close()
            self._ws = None
            self.status = 0
            # flexx.instances.sessions.pop(self) might be good,
            # but perhaps not that much need, and leaving is nice for debugging.
    
    def send_command(self, *command):
        if self._ws is not None:
            try:
                bb = serializer.encode(command)
            except Exception as err:
                print('Command that failed to encode:')
                print(command)
                raise err
            self._ws.send(bb)
    
    def instantiate_component(self, module, cname, id, args, kwargs, active_components):
        # Maybe we still have the instance?
        c = self.instances.get(id, None)
        if c is not None and c._disposed is False:
            return c
        # Find the class
        m = window.flexx.require(module)
        Cls = m[cname]  # noqa
        # Instantiate. If given, replicate the active components by which the
        # JsComponent was instantiated in Python.
        kwargs['flx_session'] = self
        kwargs['flx_id'] = id
        active_components = active_components or []
        for ac in active_components:
            ac.__enter__()
        try:
            c = Cls(*args, **kwargs)
        finally:
            for ac in reversed(active_components):
                ac.__exit__()
        return c
    
    def _register_component(self, c, id=None):
        if self.app is None:
            self.app = c  # Set our root component; is the first to register
        if id is None:
            self._component_counter += 1
            id = c.__name__ + '_' + str(self._component_counter) + 'js'
        c._id = id
        c._uid = self.id + '_' + id
        self.instances[c._id] = c
    
    def _unregister_component(self, c):
        self.instances_to_check_size.pop(c.id, None)
        pass  # c gets popped from self.instances by DISPOSE_ACK command
    
    def get_component_instance(self, id):
        """ Get instance of a Component class, or None. Or the document body
        if "body" is given.
        """
        if id == 'body':
            return window.document.body
        else:
            return self.instances.get(id, None)
    
    def init_socket(self):
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
        self.status = 2
        
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
            self.status = 0
            msg = 'Lost connection with server'
            if evt and evt.reason:
                msg += ': %s (%i)' % (evt.reason, evt.code)
            if not window.flexx.is_notebook:
                # todo: show modal or cooky-like dialog instead of killing whole page
                window.document.body.innerHTML = msg
            else:
                window.console.info(msg)
        def on_ws_error(self, evt):
            self._ws = None
            self.status = 0
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
        return self._receive_command(serializer.decode(msg))
    
    def _receive_command(self, command):
        """ Process a command send from the server.
        """
        cmd = command[0]
        if cmd == 'PING':
            # Used for roundtrip stuff, do at least one iter loop here ...
            window.setTimeout(self.send_command, 10, 'PONG', command[1])
        elif cmd == 'INIT_DONE':
            window.flexx.spin(None)
            while len(self._pending_commands):
                self._receive_raw_command(self._pending_commands.pop(0))
            self._pending_commands = None
            # print('init took', time() - self._init_time)
        elif cmd == 'PRINT':
            (window.console.ori_log or window.console.log)(command[1])
        elif cmd == 'EXEC':
            eval(command[1])
        elif cmd == 'EVAL':
            x = None
            if len(command) == 2:
                x = eval(command[1])
            elif len(command) == 3:
                x = eval('this.instances.' + command[1] + '.' + command[2])
            console.log(str(x))  # print and sends back result
        elif cmd == 'INVOKE':
            id, name, args = command[1:]
            ob = self.instances.get(id, None)
            if ob is None:
                console.warn('Cannot invoke %s.%s; '
                             'session does not know it (anymore).' % (id, name))
            elif ob._disposed is True:
                pass  # deleted, but other end might not be aware when command was send
            else:
                ob[name](*args)
        elif cmd == 'INSTANTIATE':
            self.instantiate_component(*command[1:])  # module, cname, id, args, kwargs
        elif cmd == 'DISPOSE':
            id = command[1]
            c = self.instances.get(id, None)
            if c is not None and c._disposed is False:  # else: no need to warn
                c._dispose()
            self.send_command('DISPOSE_ACK', command[1])
            self.instances.pop(id, None)  # Drop local reference now
        elif cmd == 'DISPOSE_ACK':
            self.instances.pop(command[1], None)  # Drop reference
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
                window.flexx.asset_node.appendChild(el)
            elif kind == 'CSS':
                el = window.document.createElement("style")
                el.type = "text/css"
                el.id = name
                el.innerHTML = code
                window.flexx.asset_node.appendChild(el)
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
    
    def call_after_roundtrip(self, callback, *args):
        ping_to_schedule_at = self._ping_counter + 1
        if len(self._ping_calls) == 0 or self._ping_calls[-1][0] < ping_to_schedule_at:
            window.setTimeout(self._send_ping, 0)
        self._ping_calls.push((ping_to_schedule_at, callback, args))
    
    def _send_ping(self):
        self._ping_counter += 1
        self.send_command('PING', self._ping_counter)
    
    def _receive_pong(self, count):
        while len(self._ping_calls) > 0 and self._ping_calls[0][0] <= count:
            _, callback, args = self._ping_calls.pop(0)
            window.setTimeout(callback, 0, *args)
    
    def keep_checking_size_of(self, ob, check=True):
        """ This is a service that the session provides.
        """
        if check:
            self.instances_to_check_size[ob.id] = ob
        else:
            self.instances_to_check_size.pop(ob.id, None)
    
    def _check_size_of_objects(self):
        for ob in self.instances_to_check_size.values():
            if ob._disposed is False:
                ob.check_real_size()


# In Python, we need some extras for the serializer to work
if this_is_js():
    # Include bsdf.js
    window.flexx = Flexx()
    bsdf = RawJS("flexx.require('bsdf')")
    serializer = bsdf.BsdfSerializer()
    window.flexx.serializer = serializer
else:
    # Import vendored bsdf lite module
    from . import bsdf_lite as bsdf
    serializer = bsdf.BsdfLiteSerializer()
    serializer.__module__ = __name__
