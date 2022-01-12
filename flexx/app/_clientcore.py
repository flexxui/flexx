"""
The client's core Flexx engine, implemented in PScript.
"""

from pscript import this_is_js, RawJS
from pscript.stubs import window, undefined, time, console, JSON

# This module gets transpiled to JavaScript as a whole
__pscript__ = True


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

    def spin(self, n=1):
        RawJS("""
        var el = window.document.getElementById('flexx-spinner');
        if (el) {
            if (n === null) {  // Hide the spinner overlay, now or in a bit
                if (el.children[0].innerHTML.indexOf('limited') > 0) {
                    setTimeout(function() { el.style.display = 'none'; }, 2000);
                } else {
                    el.style.display = 'none';
                }
            } else {
                for (var i=0; i<n; i++) { el.children[1].innerHTML += '&#9632'; }
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
            self._handle_error(evt)
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

        if window.performance and window.performance.navigation.type == 2:
            # Force reload when we got here with back-button, otherwise
            # an old session-id is used, see issue #530
            window.location.reload()
        elif self._validate_browser_capabilities():
            s = JsSession(app_name, session_id, ws_url)
            self._session_count += 1
            self['s' + self._session_count] = s
            self.sessions[session_id] = s

    def _validate_browser_capabilities(self):
        # We test a handful of features here, and assume that if these work,
        # all of Flexx works. It is not a hard guarantee, of course, because
        # the user can use modern features in an application.
        RawJS("""
        var el = window.document.getElementById('flexx-spinner');
        if (    window.WebSocket === undefined || // IE10+
                Object.keys === undefined || // IE9+
                false
           ) {
            var msg = ('Flexx does not support this browser.<br>' +
                       'Try Firefox, Chrome, ' +
                       'or a more recent version of the current browser.');
            if (el) { el.children[0].innerHTML = msg; }
            else { window.alert(msg); }
            return false;
        } else if (''.startsWith === undefined) { // probably IE
            var msg = ('Flexx support for this browser is limited.<br>' +
                       'Consider using Firefox, Chrome, or maybe Edge.');
            if (el) { el.children[0].innerHTML = msg; }
            return true;
        } else {
            return true;
        }
        """)

    def _handle_error(self, evt):
        msg = short_msg = evt.message
        if not window.evt:
            window.evt = evt
        if evt.error and evt.error.stack:  # evt.error can be None for syntax err
            stack = evt.error.stack.splitlines()
            # Some replacements
            session_needle = '?session_id=' + self.id
            for i in range(len(stack)):
                stack[i] = stack[i].replace('@', ' @ ').replace(session_needle, '')
            # Strip items from the start
            for x in [evt.message, '_pyfunc_op_error']:
                if x in stack[0]:
                    stack.pop(0)
            # Truncate the stack
            for i in range(len(stack)):
                for x in ['_process_actions', '_process_reactions', '_process_calls']:
                    if ('Loop.' + x) in stack[i]:
                        stack = stack[:i]
                        break
            # Pop items from in between
            for i in reversed(range(len(stack))):
                for x in ['flx_action ']:
                    if stack[i] and stack[i].count(x):
                        stack.pop(i)
            # Combine and tweak the message some more
            msg += '\n' + '\n'.join(stack)
        elif evt.message and evt.lineno:  # message, url, linenumber
            msg += "\nIn %s:%i" % (evt.filename, evt.lineno)
        # Handle error
        evt.preventDefault()  # Don't do the standard error
        window.console.ori_error(msg)
        for session in self.sessions.values():
            session.send_command("ERROR", short_msg)

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
        # Note that only toplevel widgets are tracked, and only once per sec
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
            window.document.body.textContent = 'Browser does not support WebSockets'
            raise RuntimeError("FAIL: need websocket")

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
            msg = evt.data  # bsdf-encoded command
            if not msg:
                pass  # ? drop glitchy message :/
            elif self._pending_commands is None:
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
                window.document.body.textContent = msg
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
            console.log(str(x))  # print (and thus also sends back result)
        elif cmd == 'EVALANDRETURN':
            try:
                x = eval(command[1])
            except Exception as err:
                x = str(err)
            eval_id = command[2]  # to identify the result in Python
            self.send_command("EVALRESULT", x, eval_id)
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
            code += '\n//# sourceURL=%s/flexx/assets/shared/%s\n' % (address, name)
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
        # Gets called by the Widget class for toplevel widgets. That
        # is, toplevel to Flexx: they might not be toplevel for the
        # browser. This method will make sure that they know their size
        # in any case, at least once each second.
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
