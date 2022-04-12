"""
Definition of the Session class.
"""

import re
import gc
import sys
import time
import json
import base64
import random
import hashlib
import asyncio
import weakref
import datetime
from http.cookies import SimpleCookie

from ..event._component import new_type

from ._component2 import PyComponent, JsComponent, AppComponentMeta
from ._asset import Asset, Bundle, solve_dependencies
from ._assetstore import AssetStore, INDEX
from ._assetstore import assets as assetstore
from ._clientcore import serializer
from . import logger

from .. import config

reprs = json.dumps


# Use the system PRNG for session id generation (if possible)
# NOTE: secure random string generation implementation is adapted
#       from the Django project.

def get_random_string(length=24, allowed_chars=None):
    """ Produce a securely generated random string.

    With a length of 12 with the a-z, A-Z, 0-9 character set returns
    a 71-bit value. log_2((26+26+10)^12) =~ 71 bits
    """
    allowed_chars = allowed_chars or ('abcdefghijklmnopqrstuvwxyz' +
                                      'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
    try:
        srandom = random.SystemRandom()
    except NotImplementedError:  # pragma: no cover
        srandom = random
        logger.warning('Falling back to less secure Mersenne Twister random string.')
        bogus = "%s%s%s" % (random.getstate(), time.time(), 'sdkhfbsdkfbsdbhf')
        random.seed(hashlib.sha256(bogus.encode()).digest())

    return ''.join(srandom.choice(allowed_chars) for i in range(length))


class Session:
    """ A connection between Python and the client runtime (JavaScript).

    The session is what holds together the app widget, the web runtime,
    and the websocket instance that connects to it.

    Responsibilities:

    * Send messages to the client and process messages received by the client.
    * Keep track of PyComponent instances used by the session.
    * Keep track of JsComponent instances associated with the session.
    * Ensure that the client has all the module definitions it needs.

    """

    STATUS = new_type('Enum', (), {'PENDING': 1, 'CONNECTED': 2, 'CLOSED': 0})

    def __init__(self, app_name, store=None,
                 request=None):  # Allow custom store for testing
        self._store = store if (store is not None) else assetstore
        assert isinstance(self._store, AssetStore)

        self._creation_time = time.time()  # used by app manager

        # Id and name of the app
        self._id = get_random_string()
        self._app_name = app_name

        # To keep track of what modules are defined at the client
        self._present_classes = set()  # Component classes known by the client
        self._present_modules = set()  # module names that, plus deps
        self._present_assets = set()  # names of used associated assets
        self._assets_to_ignore = set()  # user settable

        # Data for this session (in addition to the data provided by the store)
        self._data = {}

        # More vars
        self._runtime = None  # init web runtime, will be set when used
        self._ws = None  # init websocket, will be set when a connection is made
        self._closing = False  # Flag to help with shutdown

        # PyComponent or JsComponent instance, can be None if app_name is __default__
        self._component = None

        # The session assigns component id's and keeps track of component objects
        self._component_counter = 0
        self._component_instances = weakref.WeakValueDictionary()
        self._dead_component_ids = set()

        # Keep track of roundtrips. The _ping_calls elements are:
        # [ping_count, {objects}, *(callback, args)]
        self._ping_calls = []
        self._ping_counter = 0
        self._eval_result = {}
        self._eval_count = 0

        # While the client is not connected, we keep a queue of
        # commands, which are send to the client as soon as it connects
        self._pending_commands = []

        # request related information
        self._request = request
        if request and request.cookies:
            cookies = request.cookies
        else:
            cookies = {}
        self._set_cookies(cookies)

    def __repr__(self):
        t = '<%s for %r (%i) at 0x%x>'
        return t % (self.__class__.__name__, self.app_name, self.status, id(self))

    @property
    def request(self):
        """The tornado request that was at the origin of this session.
        """
        return self._request

    @property
    def id(self):
        """ The unique identifier of this session.
        """
        return self._id

    @property
    def app_name(self):
        """ The name of the application that this session represents.
        """
        return self._app_name

    @property
    def app(self):
        """ The root PyComponent or JsComponent instance that represents the app.
        """
        return self._component

    @property
    def runtime(self):
        """ The runtime that is rendering this app instance. Can be
        None if the client is a browser.
        """
        return self._runtime

    @property
    def status(self):
        """ The status of this session.
        The lifecycle for each session is:

        * status 1: pending
        * status 2: connected
        * status 0: closed
        """
        if self._ws is None:
            return self.STATUS.PENDING  # not connected yet
        elif self._ws.close_code is None:
            return self.STATUS.CONNECTED  # alive and kicking
        else:
            return self.STATUS.CLOSED  # connection closed

    @property
    def present_modules(self):
        """ The set of module names that is (currently) available at the client.
        """
        return set(self._present_modules)

    @property
    def assets_to_ignore(self):
        """ The set of names of assets that should *not* be pushed to
        the client, e.g. because they are already present on the page.
        Add names to this set to prevent them from being loaded.
        """
        return self._assets_to_ignore

    def close(self):
        """ Close the session: close websocket, close runtime, dispose app.
        """
        # Stop guarding objects to break down any circular refs
        self._ping_calls = []
        self._closing = True  # suppress warnings for session being closed.
        try:
            # Close the websocket
            if self._ws:
                self._ws.close_this()
            # Close the runtime
            if self._runtime:
                self._runtime.close()
            # Dispose the component and break the circular reference
            if self._component is not None:
                self._component.dispose()
                self._component = None
            # Discard data
            self._data = {}
            # This might be a good time to invoke the gc
            gc.collect()
        finally:
            self._closing = False

    ## Hooking up with app, websocket, runtime

    def _set_ws(self, ws):
        """ A session is always first created, so we know what page to
        serve. The client will connect the websocket, and communicate
        the session_id so it can be connected to the correct Session
        via this method
        """
        if self._ws is not None:
            raise RuntimeError('Session is already connected.')
        # Set websocket object - this is what changes the status to CONNECTED
        self._ws = ws
        self._ws.write_command(("PRINT", "Flexx session says hi"))
        # Send pending commands
        for command in self._pending_commands:
            self._ws.write_command(command)
        self._ws.write_command(('INIT_DONE', ))

    def _set_cookies(self, cookies=None):
        """ To set cookies, must be an http.cookie.SimpleCookie object.
        When the app is loaded as a web app, the cookies are set *before* the
        main component is instantiated. Otherwise they are set when the websocket
        is connected.
        """
        self._cookies = cookies if cookies else SimpleCookie()

    def _set_runtime(self, runtime):
        if self._runtime is not None:
            raise RuntimeError('Session already has a runtime.')
        self._runtime = runtime

    ## Cookies, mmm

    def get_cookie(self, name, default=None, max_age_days=31, min_version=None):
        """ Gets the value of the cookie with the given name, else default.
        Note that cookies only really work for web apps.
        """
        from tornado.web import decode_signed_value
        if name in self._cookies:
            value = self._cookies[name].value
            value = decode_signed_value(config.cookie_secret,
                                       name, value, max_age_days=max_age_days,
                                       min_version=min_version)
            return value.decode()
        else:
            return default

    def set_cookie(self, name, value, expires_days=30, version=None,
                   domain=None, expires=None, path="/", **kwargs):
        """ Sets the given cookie name/value with the given options. Set value
        to None to clear. The cookie value is secured using
        `flexx.config.cookie_secret`; don't forget to set that config
        value in your server. Additional keyword arguments are set on
        the Cookie.Morsel directly.
        """
        # This code is taken (in modified form) from the Tornado project
        # Copyright 2009 Facebook
        # Licensed under the Apache License, Version 2.0

        # Assume tornado is available ...
        from tornado.escape import native_str
        from tornado.httputil import format_timestamp
        from tornado.web import create_signed_value

        # Clear cookie?
        if value is None:
            value = ""
            expires = datetime.datetime.utcnow() - datetime.timedelta(days=365)
        else:
            secret = config.cookie_secret
            value = create_signed_value(secret, name, value, version=version,
                                        key_version=None)

        # The cookie library only accepts type str, in both python 2 and 3
        name = native_str(name)
        value = native_str(value)
        if re.search(r"[\x00-\x20]", name + value):
            # Don't let us accidentally inject bad stuff
            raise ValueError("Invalid cookie %r: %r" % (name, value))
        if name in self._cookies:
            del self._cookies[name]
        self._cookies[name] = value
        morsel = self._cookies[name]
        if domain:
            morsel["domain"] = domain
        if expires_days is not None and not expires:
            expires = datetime.datetime.utcnow() + datetime.timedelta(
                days=expires_days)
        if expires:
            morsel["expires"] = format_timestamp(expires)
        if path:
            morsel["path"] = path
        for k, v in kwargs.items():
            if k == 'max_age':
                k = 'max-age'
            # skip falsy values for httponly and secure flags because
            # SimpleCookie sets them regardless
            if k in ['httponly', 'secure'] and not v:
                continue
            morsel[k] = v

        self.send_command('EXEC', 'document.cookie = "%s";' %
                   morsel.OutputString().replace('"', '\\"'))

    ## Data

    def add_data(self, name, data):
        """ Add data to serve to the client (e.g. images), specific to this
        session. Returns the link at which the data can be retrieved.
        Note that actions can be used to send (binary) data directly
        to the client (over the websocket).

        Parameters:
            name (str): the name of the data, e.g. 'icon.png'. If data has
                already been set on this name, it is overwritten.
            data (bytes): the data blob.

        Returns:
            str: the (relative) url at which the data can be retrieved.
        """
        if not isinstance(name, str):
            raise TypeError('Session.add_data() name must be a str.')
        if name in self._data:
            raise ValueError('Session.add_data() got existing name %r.' % name)
        if not isinstance(data, bytes):
            raise TypeError('Session.add_data() data must be bytes.')
        self._data[name] = data
        return 'flexx/data/%s/%s' % (self.id, name)  # relative path for  export

    def remove_data(self, name):
        """ Remove the data associated with the given name. If you need this,
        consider using actions instead. Note that data is automatically
        released when the session is closed.
        """
        self._data.pop(name, None)

    def get_data_names(self):
        """ Get a list of names of the data provided by this session.
        """
        return list(self._data.keys())

    def get_data(self, name):
        """ Get the data corresponding to the given name. This can be
        data local to the session, or global data. Returns None if data
        by that name is unknown.
        """
        if True:
            data = self._data.get(name, None)
        if data is None:
            data = self._store.get_data(name)
        return data

    def _dump_data(self):
        """ Get a dictionary that contains all data specific to this session.
        The keys represent relative paths, the values are all bytes.
        Private method, used by App.dump().
        """
        d = {}
        for fname in self.get_data_names():
            d['flexx/data/{}/{}'.format(self.id, fname)] = self.get_data(fname)
        return d

    ## Keeping track of component objects

    def _register_component(self, component, id=None):
        """ Called by PyComponent and JsComponent to give them an id
        and register with the session.
        """
        assert isinstance(component, (PyComponent, JsComponent))
        assert component.session is self
        cls = component.__class__
        if self._component is None:
            self._component = component  # register root component (i.e. the app)
        # Set id
        if id is None:
            self._component_counter += 1
            id = cls.__name__ + '_' + str(self._component_counter)
        component._id = id
        component._uid = self.id + '_' + id
        # Register the instance using a weakref
        self._component_instances[component._id] = component
        # Register the class to that the client has the needed definitions
        self._register_component_class(cls)
        self.keep_alive(component)

    def _unregister_component(self, component):
        self._dead_component_ids.add(component.id)
        # self.keep_alive(component)  # does not work on pypy; deletion in final
        # Because we use weak refs, and we want to be able to keep (the id of)
        # the object so that INVOKE on it can be silently ignored (because it
        # is disposed). The object id gets removed by the DISPOSE_ACK command.

    def get_component_instance(self, id):
        """ Get PyComponent or JsComponent instance that is associated with
        this session and has the corresponding id. The returned value can be
        None if it does not exist, and a returned component can be disposed.
        """
        return self._component_instances.get(id, None)

    ## JIT asset definitions

    def _register_component_class(self, cls):
        """ Mark the given PyComponent or JsComponent class as used; ensure
        that the client knows about the module that it is defined in,
        dependencies of this module, and associated assets of any of these
        modules.
        """
        if not (isinstance(cls, type) and issubclass(cls, (PyComponent, JsComponent))):
            raise TypeError('_register_component_class() needs a PyComponent '
                            'or JsComponent class')
        # Early exit if we know the class already
        if cls in self._present_classes:
            return

        # Make sure that no two Component classes have the same name, or we get problems
        # that are difficult to debug. Unless classes are defined interactively.
        # The modules of classes that are re-registered are re-defined. The base
        # class of such a component is assumed to be either unchanged or defined
        # in the same module. It can also happen that a class is registered for
        # which the module was defined earlier (e.g. ui.html). Such modules
        # are redefined as well.
        same_name = [c for c in self._present_classes if c.__name__ == cls.__name__]
        if same_name:
            is_interactive = self._app_name == '__default__'
            same_name.append(cls)
            is_dynamic_cls = all([c.__module__ == '__main__' for c in same_name])
            if not (is_interactive and is_dynamic_cls):
                raise RuntimeError('Cannot have multiple Component classes with '
                                   'the same name unless using interactive session '
                                   'and the classes are dynamically defined: %r'
                                   % same_name)

        # Mark the class and the module as used
        logger.debug('Registering Component class %r' % cls.__name__)
        self._register_module(cls.__jsmodule__)

    def _register_module(self, mod_name):
        """ Register a module with the client, as well as its
        dependencies, and associated assests of the module and its
        dependencies. If the module was already defined, it is
        re-defined.
        """

        if (mod_name.startswith(('flexx.app', 'flexx.event')) and
                                                '.examples' not in mod_name):
            return  # these are part of flexx core assets

        modules = set()
        assets = []

        def collect_module_and_deps(mod):
            if mod.name.startswith(('flexx.app', 'flexx.event')):
                return  # these are part of flexx core assets
            if mod.name not in self._present_modules:
                self._present_modules.add(mod.name)
                for dep in mod.deps:
                    if dep.startswith(('flexx.app', 'flexx.event')):
                        continue
                    submod = self._store.modules[dep]
                    collect_module_and_deps(submod)
                modules.add(mod)

        # Collect module and dependent modules that are not yet defined
        self._store.update_modules()  # Ensure up-to-date module definition
        mod = self._store.modules[mod_name]
        collect_module_and_deps(mod)
        f = lambda m: (m.name.startswith('__main__'), m.name)
        modules = solve_dependencies(sorted(modules, key=f))

        # Collect associated assets
        for mod in modules:
            for asset_name in self._store.get_associated_assets(mod.name):
                if asset_name not in self._present_assets:
                    self._present_assets.add(asset_name)
                    assets.append(self._store.get_asset(asset_name))
        # If the module was already defined and thus needs to be re-defined,
        # we only redefine *this* module, no deps and no assoctated assets.
        if not modules:
            modules.append(mod)
        # Collect CSS and JS assets
        for mod in modules:
            if mod.get_css().strip():
                assets.append(self._store.get_asset(mod.name + '.css'))
        for mod in modules:
            assets.append(self._store.get_asset(mod.name + '.js'))

        # Mark classes as used
        for mod in modules:
            for cls in mod.component_classes:
                self._present_classes.add(cls)

        # Push assets over the websocket. Note how this works fine with the
        # notebook because we turn ws commands into display(HTML()).
        # JS can be defined via eval() or by adding a <script> to the DOM.
        # The latter allows assets that do not use strict mode, but sourceURL
        # does not work on FF. So we only want to eval our own assets.
        for asset in assets:
            if asset.name in self._assets_to_ignore:
                continue
            logger.debug('Loading asset %s' % asset.name)
            # Determine command suffix. All our sources come in bundles,
            # for which we use eval because it makes sourceURL work on FF.
            # (It does not work in Chrome in either way.)
            suffix = asset.name.split('.')[-1].upper()
            if suffix == 'JS' and isinstance(asset, Bundle):
                suffix = 'JS-EVAL'
            self.send_command('DEFINE', suffix, asset.name, asset.to_string())

    ## Communication with the client

    def send_command(self, *command):
        """ Send a command to the other side. Commands consists of at least one
        argument (a string representing the type of command).
        """
        assert len(command) >= 1
        if self._closing:
            pass
        elif self.status == self.STATUS.CONNECTED:
            self._ws.write_command(command)
        elif self.status == self.STATUS.PENDING:
            self._pending_commands.append(command)
        else:
            #raise RuntimeError('Cannot send commands; app is closed')
            logger.warning('Cannot send commands; app is closed')

    def _receive_command(self, command):
        """ Received a command from JS.
        """
        cmd = command[0]
        if cmd == 'EVALRESULT':
            self._eval_result[command[2]] = command[1]
        elif cmd == 'PRINT':
            print('JS:', command[1])
        elif cmd == 'INFO':
            logger.info('JS: ' + command[1])
        elif cmd == 'WARN':
            logger.warning('JS: ' + command[1])
        elif cmd == 'ERROR':
            logger.error('JS: ' + command[1] +
                         ' - stack trace in browser console (hit F12).')
        elif cmd == 'INVOKE':
            id, name, args = command[1:]
            ob = self.get_component_instance(id)
            if ob is None:
                if id not in self._dead_component_ids:
                    t = 'Cannot invoke %s.%s; session does not know it (anymore).'
                    logger.warning(t % (id, name))
            elif ob._disposed:
                pass  # JS probably send something before knowing the object was dead
            else:
                func = getattr(ob, name, None)
                if func:
                    func(*args)
        elif cmd == 'PONG':
            self._receive_pong(command[1])
        elif cmd == 'INSTANTIATE':
            modulename, cname, id, args, kwargs = command[1:]
            # Maybe we still have the instance?
            c = self.get_component_instance(id)
            if c and not c._disposed:
                self.keep_alive(c)
                return
            # Try to find the class
            m, cls, e = None, None, 0
            if modulename in assetstore.modules:
                m = sys.modules[modulename]
                cls = getattr(m, cname, None)
                if cls is None:
                    e = 1
                elif not (isinstance(cls, type) and issubclass(cls, JsComponent)):
                    cls, e = None, 2
                elif cls not in AppComponentMeta.CLASSES:
                    cls, e = None, 3
            if cls is None:
                raise RuntimeError('Cannot INSTANTIATE %s.%s (%i)' %
                                   (modulename, cname, e))
            # Instantiate
            kwargs['flx_session'] = self
            kwargs['flx_id'] = id
            assert len(args) == 0
            c = cls(**kwargs)  # calls keep_alive via _register_component()
        elif cmd == 'DISPOSE':  # Gets send from local to proxy
            id = command[1]
            c = self.get_component_instance(id)
            if c and not c._disposed:  # no need to warn if component does not exist
                c._dispose()
            self.send_command('DISPOSE_ACK', command[1])
            self._component_instances.pop(id, None)  # Drop local ref now
        elif cmd == 'DISPOSE_ACK':  # Gets send from proxy to local
            self._component_instances.pop(command[1], None)
            self._dead_component_ids.discard(command[1])
        else:
            logger.error('Unknown command received from JS:\n%s' % command)

    def keep_alive(self, ob, iters=1):
        """ Keep an object alive for a certain amount of time, expressed
        in Python-JS ping roundtrips. This is intended for making JsComponent
        (i.e. proxy components) survice the time between instantiation
        triggered from JS and their attachement to a property, though any type
        of object can be given.
        """
        ping_to_schedule_at = self._ping_counter + iters
        el = self._get_ping_call_list(ping_to_schedule_at)
        el[1][id(ob)] = ob  # add to dict of objects to keep alive

    def call_after_roundtrip(self, callback, *args):
        """ A variant of ``call_soon()`` that calls a callback after
        a py-js roundrip. This can be convenient to delay an action until
        after other things have settled down.
        """
        # The ping_counter represents the ping count that is underway.
        # Since we want at least a full ping, we want one count further.
        ping_to_schedule_at = self._ping_counter + 1
        el = self._get_ping_call_list(ping_to_schedule_at)
        el.append((callback, args))

    async def co_roundtrip(self):
        """ Coroutine to wait for one Py-JS-Py roundtrip.
        """
        count = 0
        def up():
            nonlocal count
            count += 1
        self.call_after_roundtrip(up)
        while count < 1:
            await asyncio.sleep(0.02)

    async def co_eval(self, js):
        """ Coroutine to evaluate JS in the client, wait for the result,
        and then return it. It is recomended to use this method only
        for testing purposes.
        """
        id = self._eval_count
        self._eval_count += 1
        self.send_command('EVALANDRETURN', js, id)
        while id not in self._eval_result:
            await asyncio.sleep(0.2)
        return self._eval_result.pop(id)

    def _get_ping_call_list(self, ping_count):
        """ Get an element from _ping_call for the specified ping_count.
        The element is a list [ping_count, {objects}, *(callback, args)]
        """
        # No pending ping_calls?
        if len(self._ping_calls) == 0:
            # Start pinging
            send_ping_later(self)
            # Append element
            el = [ping_count, {}]
            self._ping_calls.append(el)
            return el

        # Try to find existing element, or insert it
        for i in reversed(range(len(self._ping_calls))):
            el = self._ping_calls[i]
            if el[0] == ping_count:
                return el
            elif el[0] < ping_count:
                el = [ping_count, {}]
                self._ping_calls.insert(i + 1, el)
                return el
        else:
            el = [ping_count, {}]
            self._ping_calls.insert(0, el)
            return el

    def _receive_pong(self, count):
        # Process ping calls
        while len(self._ping_calls) > 0 and self._ping_calls[0][0] <= count:
            _, objects, *callbacks = self._ping_calls.pop(0)
            objects.clear()
            del objects
            for callback, args in callbacks:
                asyncio.get_event_loop().call_soon(callback, *args)
        # Continue pinging?
        if len(self._ping_calls) > 0:
            send_ping_later(self)

def send_ping_later(session):
    # This is to prevent the prevention of the session from being discarded due
    # to a ref lingering in an asyncio loop.
    def x(weaksession):
        s = weaksession()
        if s is not None and s.status > 0:
            s._ping_counter += 1
            s.send_command('PING', s._ping_counter)
    # asyncio.get_event_loop().call_soon(x, weakref.ref(session))
    asyncio.get_event_loop().call_later(0.01, x, weakref.ref(session))


## Functions to get page
# These could be methods, but are only for internal use

def get_page(session):
    """ Get the string for the HTML page to render this session's app.
    Not a lot; all other JS and CSS assets are pushed over the websocket.
    """
    css_assets = [assetstore.get_asset('reset.css')]
    js_assets = [assetstore.get_asset('flexx-core.js')]
    return _get_page(session, js_assets, css_assets, 3, False)


def get_page_for_export(session, commands, link=0):
    """ Get the string for an exported HTML page (to run without a server).
    In this case, there is no websocket to push JS/CSS assets over; these
    need to be included inside or alongside the main html page.
    """
    # This function basically collects all assets that the session needs,
    # creates a special -export.js asset that executes the given commands,
    # and puts it al together using _get_page().

    # We start as a normal page ...
    css_assets = [assetstore.get_asset('reset.css')]
    js_assets = [assetstore.get_asset('flexx-core.js')]

    # Get all the used modules
    modules = [assetstore.modules[name] for name in session.present_modules]
    f = lambda m: (m.name.startswith('__main__'), m.name)
    modules = solve_dependencies(sorted(modules, key=f))
    # First the associated assets
    asset_names = set()
    for mod in modules:
        for asset_name in assetstore.get_associated_assets(mod.name):
            if asset_name not in asset_names:
                asset_names.add(asset_name)
                asset = assetstore.get_asset(asset_name)
                if asset.name.lower().endswith('.js'):
                    js_assets.append(asset)
                else:
                    css_assets.append(asset)
    # Then the modules themselves
    for mod in modules:
        if mod.get_css().strip():
            css_assets.append(assetstore.get_asset(mod.name + '.css'))
    for mod in modules:
        js_assets.append(assetstore.get_asset(mod.name + '.js'))

    # Create asset for launching the app (commands that normally get send
    # over the websocket)
    lines = []
    lines.append('flexx.is_exported = true;\n')
    lines.append('flexx.run_exported_app = function () {')
    lines.append('    var commands_b64 = [')
    for command in commands:
        if command[0] != 'DEFINE':
            command_str = base64.encodebytes(serializer.encode(command)).decode()
            lines.append('        "' + command_str.replace('\n', '') + '",')
    lines.append('        ];')
    lines.append('    bb64 =  flexx.require("bb64");')
    lines.append('    for (var i=0; i<commands_b64.length; i++) {')
    lines.append('        var command = flexx.serializer.decode('
                                            'bb64.decode(commands_b64[i]));')
    lines.append('        flexx.s1._receive_command(command);')
    lines.append('    }\n};\n')
    # Create a session asset for it, "-export.js" is always embedded
    export_asset = Asset('flexx-export.js', '\n'.join(lines))
    js_assets.append(export_asset)

    # Combine it all
    return _get_page(session, js_assets, css_assets, link, True)


def _get_page(session, js_assets, css_assets, link, export):
    """ Compose index page. Depending on the value of link and the types
    of assets, the assets are either embedded or linked.
    """
    pre_path = 'flexx/assets' if export else '/flexx/assets'  # relative / abs

    codes = []

    for assets in [css_assets, js_assets]:
        for asset in assets:
            if link in (0, 1):
                html = asset.to_html('{}', link)
            else:
                if asset.name.endswith(('-info.js', '-export.js')):
                    # Special case, is always embedded, see get_page_for_export()
                    html = asset.to_html('', 0)
                else:
                    html = asset.to_html(pre_path + '/shared/{}', link)
            codes.append(html)
            if export and assets is js_assets:
                codes.append('<script>window.flexx.spin();</script>')
        codes.append('')  # whitespace between css and js assets

    codes.append('<script>flexx.create_session("%s", "%s");</script>\n' %
                 (session.app_name, session.id))

    src = INDEX
    if link in (0, 1):
        asset_names = [a.name for a in css_assets + js_assets]
        toc = '<!-- Contents:\n\n- ' + '\n- '.join(asset_names) + '\n\n-->'
        codes.insert(0, toc)
        src = src.replace('ASSET-HOOK', '\n\n\n'.join(codes))
    else:
        src = src.replace('ASSET-HOOK', '\n'.join(codes))

    return src
