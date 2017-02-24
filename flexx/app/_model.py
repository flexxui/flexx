"""
Base class for objects that live in both Python and JS. This basically
implements the syncing of properties and events.

Developer info:

Events are transparently handled accross the language barrier. Both sides
keep each-other informed for what events there are registered handlers, and
only those events are "synchronised". That way, a mouse move event does
not result in a lot of messages send to Python (unless there is a mouse move
handler in Python).

The Model class provides three ways for adding properties:

* a property defined at the Python side
* a property defined at the JS side
* a property defined at both sides (defined as part of Python class,
  but with flag `both=True`)

In the first two cases, a corresponding proxy property is created for
the other side. The property is settable at both ends (unless its a
readonly), but the property is validated where it is defined; the proxy
sends the new value to the other side, where validation takes places,
after which the normalized value is send back and set. The event for
setting a property is emitted by the properties directly, i.e. events
for properties are not "synchronised", but occur on both sides because
properties are synchronised.

In the situation where the `both` flag is used, validation occurs on
both sides. Such a property is directly validated and "applied" at the
side where it is set, and the value is synchronised to the other side,
where its again validated and set.

Properties are eventually synchronous. This means that they may become
out of sync, e.g. when set nearly at the same time in both JS and
Python, but will become equal after a certain time. In the first two
cases eventual synchronicity is naturally occuring because there is a
clear "reference" side. In the third case eventual synchronicity is
implemented by making Python the end-point: setting a property at the
JS side will also set it to the Python side, and setting a property at
the Python side will set the property in JS, which will set (again) in
Python. Note that setting a property with the same value will not cause
an event to be emitted.

The Python side was chosen as the end-point because at this side any
jitter from quickly updating properties generally has little side-effects,
while on the JS side you will see it occuring even for a slider. There
means to avoid jitter, but this complicates the code. We could add it
if it's found to be necessarty at a later time.

Properties can be explicitly marked to not sync. This can be used e.g.
in cases where it does not make sense to have the property value
available at the other side.

Most of the logic for determining when the setting-of-a-property must
be synchronised to the other ends is implemented in the ``_set_prop()``
methods.

Initialization of properties was a pain to get right. Without going
into too much detail, the ``init()`` method on both the Python and JS
side provide a means for subclasses to do initialization at a time when
the property values have their initial values, but handlers are not yet
initialized and events are not yet emitted. Therefore additional
attributes and handlers can be created here.

"""

import sys
import json
import threading

from .. import event
from ..event._hasevents import (with_metaclass, new_type, HasEventsMeta,
                                finalize_hasevents_class)
from ..event._emitters import Emitter
from ..event._js import create_js_hasevents_class, HasEventsJS
from ..pyscript import js_rename, window, JSString

from ._asset import get_mod_name
from ._server import call_later
from . import logger

# The clientcore module is a PyScript module that forms the core of the
# client-side of Flexx. We import the serializer instance, and can use
# that name in both Python and JS. Of course, in JS it's just the
# corresponding instance from the module that's being used.
# By using something from clientcore in JS here, we make clientcore a
# dependency of the the current module.
from ._clientcore import serializer

manager = None  # Set by __init__ to prevent circular dependencies

reprs = json.dumps


def get_model_classes():
    """ Get a list of all known Model subclasses.
    """
    return [c for c in ModelMeta.CLASSES if issubclass(c, Model)]


# Keep track of a stack of "active" models for use within context
# managers. We have one list for each thread. Note that we should limit
# its use to context managers, and execution should never be handed back
# to the Tornado event loop while inside a context.
_active_models_per_thread = {}  # dict of threadid -> list

def _get_active_models():
    """ Get list that represents the stack of "active" models.
    Each thread has its own stack. Should only be used directly inside
    a Model context manager.
    """
    # Get thread id
    if hasattr(threading, 'current_thread'):
        tid = id(threading.current_thread())
    else:  # pragma: no cover
        tid = id(threading.currentThread())
    # Get list of parents for this thread
    return _active_models_per_thread.setdefault(tid, [])


def get_active_models():
    """ Get a tuple of Model instance that represent the stack of "active"
    models. Each thread has its own stack. Also see get_active_model().
    """
    return tuple(_get_active_models())


def get_active_model():
    """ If the execution is now in a Model context manager, return the
    corresponding object, and None otherwise. Can be used by subclasses
    to implement parenting-like behaviour using the with-statement.
    """
    models = _get_active_models()
    if models:
        return models[-1]
    else:
        session = manager.get_default_session()
        if session is not None:
            return session.app


def stub_emitter_func_py(self, *args):
    raise RuntimeError('This emitter can only be called from JavaScript')


class ModelMeta(HasEventsMeta):
    """ Meta class for Model
    Set up proxy properties in Py/JS.
    """
    
    # Keep track of all subclasses
    CLASSES = []
    
    def __init__(cls, cls_name, bases, dct):
        
        # Register this class and make PyScript convert the name
        ModelMeta.CLASSES.append(cls)
        
        OK_MAGICS = '__init__', '__json__', '__from_json__'
        
        # We have three classes: the main class (cls) on which the user
        # defines things that apply only to Python, cls.JS for things
        # that apply only to JavaScript, and cls.Both to things that
        # apply to both. The class attributes of the latter must be
        # copied to the former two classes.
        
        # Implicit inheritance for JS "subclass"
        jsbases = [getattr(b, 'JS') for b in cls.__bases__ if hasattr(b, 'JS')]
        JS = new_type('JS', tuple(jsbases), {})
        if 'JS' in cls.__dict__:
            if '__init__' in cls.JS.__dict__:
                JS.__init__ = cls.JS.__init__
            for name, val in cls.JS.__dict__.items():
                if not name.startswith('__'):
                    bettername = name.replace('_JS__', '_' + cls.__name__ + '__')
                    setattr(JS, bettername, val)
                elif name in OK_MAGICS:
                    setattr(JS, name, val)
        cls.JS = JS  # finalize_hasevents_class(JS)
        
        # Ensure that this class has a Both "subclass"
        if 'Both' not in cls.__dict__:
            Both = new_type('Both', (), {})
            setattr(cls, 'Both', Both)
        
        # Copy properties from Both class to main class and JS class. Note that
        # in Python 3.6 we iterate in the order in which the items are defined,
        # though we currently do not preserve the order of Both/JS.
        for name, val in cls.Both.__dict__.items():
            if name.startswith('__') and name.endswith('__'):
                continue
            if name in cls.JS.__dict__:  # hasattr(cls.JS, name) is overloading
                raise TypeError('Common attribute %r on %s clashes with JS '
                                'attribute.' % (name, cls.__name__))
            elif name in cls.__dict__:
                raise TypeError('Common property %r on %s clashes with Python '
                                'attribute.' % (name, cls.__name__))
            else:
                setattr(cls.JS, name, val)
                setattr(cls, name, val)
        
        # Create stub emitters on main class (for docs on events)
        for name, val in cls.JS.__dict__.items():
            if isinstance(val, Emitter) and not hasattr(cls, name):
                p = val.__class__(stub_emitter_func_py, name, val._func.__doc__)
                setattr(cls, name, p)
        
        # Finalize classes
        finalize_hasevents_class(JS)
        HasEventsMeta.__init__(cls, cls_name, bases, dct)
        
        # Add lists for local properties
        cls.__local_properties__ = [name for name in cls.__properties__
                    if getattr(cls, name) is not getattr(cls.JS, name, None)]
        cls.JS.__local_properties__ = [name for name in cls.JS.__properties__
                    if getattr(cls.JS, name) is not getattr(cls, name, None)]
        
        # Write __jsmodule__; an optimization for our module/asset system
        cls.__jsmodule__ = get_mod_name(sys.modules[cls.__module__])
        
        # Set JS, META, and CSS for this class
        cls.JS.CODE = cls._get_js()
        cls.CSS = cls.__dict__.get('CSS', '')
    
    def _get_js(cls):
        """ Get source code for this class plus the meta info about the code.
        """
        # Since classes are defined in a module, we can safely name the classes
        # by their plain name. But flexx.classes.X remains the "official" 
        # namespace, so that things work easlily accross modules, and we can
        # even re-define classes (e.g. in the notebook).
        cls_name = cls.__name__
        base_class = 'flexx.classes.%s.prototype' % cls.mro()[1].__name__
        code = []
        # Add JS version of HasEvents when this is the Model class
        if cls.mro()[1] is event.HasEvents:
            c = js_rename(HasEventsJS.JSCODE, 'HasEvents', 'flexx.classes.HasEvents')
            code.append(c)
        # Add this class
        c = create_js_hasevents_class(cls.JS, cls_name, base_class)
        meta = c.meta
        code.append(c.replace('var %s =' % cls_name,
                              'var %s = flexx.classes.%s =' % (cls_name, cls_name),
                              1))
        if cls.mro()[1] is event.HasEvents:
            code.append('flexx.serializer.add_reviver("Flexx-Model",'
                        ' flexx.classes.Model.prototype.__from_json__);\n')
        # Return with meta info
        js = JSString('\n'.join(code))
        js.meta = meta
        return js


class Model(with_metaclass(ModelMeta, event.HasEvents)):
    """ Subclass of HasEvents representing Python-JavaScript object models.
    
    Each instance of this class has a corresponding object in
    JavaScript. Events are transparently handled accross the language
    barrier. To avoid unnecessary communication, only events for which
    there are handlers at the other side are synchronized.
    
    The JS version of this class is defined by the contained ``JS``
    class. One can define methods, properties, handlers, and (json
    serializable) constants on the JS class.
    
    One can also make use of a contained ``Both`` class to define things
    that will be present in both Python and JS. This is intended primarily
    for defining properties, which can be set on both ends, and which get
    automatically synchronised.
    
    The ``init()`` method on both the Python and JS side can be used
    to do initialization at a time when properties have their initial
    values, but handlers are not yet initialized and events are not yet
    emitted. When a Model instance is assigned as an attribute to the Python
    instance (inside the init() method), the corresponding attribute
    will also be present at the JavaScript side.
    
    Initialization order and life cycle:
    
    * An id and session are associated with the model.
    * The default/initial values for the properties are set.
    * The init() is called. You can get/set properties and attributes here.
    * The handlers are connected. You can use properties here, as well
      as attributes set in init(). Handlers connected to events that
      correspond to a property receive an event to communicate the
      initial value (unless that property does not have a value yet).
    * On the JavaScript side the same order applies. The creation of
      the JavaScript object occurs after the Python object is created.
    * The JavaScript part of a Model is not garbadge collected, but removed
      when the Python side object is deleted or disposed using dispose().
    * The Python part of a model is garbadge collected as usual. Note that
      handlers hold references to the objects that they connect to.
    * Note that the Widget class has a mechanism to avoid being deleted
      when it is temporarily not referenced due to jitter in the
      children property.
    
    Models can be used as a context manager to make new Model objects
    created inside such a context to share the same session. The ``init()``
    method is invoked in the context of the object itself.
    
    The typical way to use a model is do define properties (preferably
    in the Both "subclass") and events, and react to these by writing
    handlers at the side where the action should be taken. See the example
    below or many of the examples of the Flexx documentation.
    
    Parameters:
        session (Session, None): the session object that connects this
            instance to a JS client. If not given, will use the session
            of a currently active model (i.e. as a context manager).
        is_app (bool): whether this object is the main app object. Set
            by Flexx internally. Not used by the Model class, but can
            be used by subclasses.
        kwargs: initial property values (see HasEvents).
    
    Notes:
        This class provides the base object for all widget classes in
        ``flexx.ui``. However, one can also create subclasses that have
        nothing to do with user interfaces or DOM elements. 
    
    Example:
    
        .. code-block:: py
        
            class MyModel(Model):
                
                @event.connect('foo')
                def handle_changes_to_foo_in_python(self, *events):
                    ...
                
                class Both:
                
                    @event.prop
                    def foo(self, v=0):
                        return float(v)
                
                class JS:
                    
                    BAR = [1, 2, 3]
                    
                    def handle_changes_to_foo_in_js(self, *events):
                        ...
    """
    
    # CSS for this class (no css in the base class)
    CSS = ""
    
    def __init__(self, *init_args, **kwargs):
        
        # Pop args that we need from the kwargs (because legacy Python does not
        # support keyword args after *args). Param "is_app" is not used here,
        # but we "take" the argument so it is not mistaken for a property value.
        session = kwargs.pop('session', None)
        kwargs.pop('is_app', None)
        
        # Init session
        if session is None:
            active_model = get_active_model()
            if active_model is not None:
                session = active_model.session
        if session is None:
            raise RuntimeError('Cannot instantiate Model %s without a session'
                               % self.__class__.__name__)
        self._session = session
        
        # Register this model with the session. Sets the id.
        session._register_model(self)
        
        # Get initial event connections
        event_types_py, event_types_js = [], []
        for handler_name in self.__handlers__:
            descriptor = getattr(self.__class__, handler_name)
            event_types_py.extend(descriptor.local_connection_strings)
        for handler_name in self.JS.__handlers__:
            descriptor = getattr(self.JS, handler_name)
            event_types_js.extend(descriptor.local_connection_strings)
        
        # Get event types that we need to register that may come from other end
        known_event_types_py = self.__emitters__ + self.__local_properties__
        known_event_types_js = self.JS.__emitters__ + self.JS.__local_properties__
        
        # Further initialization of attributes
        self.__event_types_js = event_types_js
        self.__pending_events_from_js = []
        self.__pending_props_from_js = []
        
        # Instantiate JavaScript version of this class
        clsname = 'flexx.classes.' + self.__class__.__name__
        cmd = 'flexx.instances.%s = new %s(%s, %s, %s);' % (
                self._id, clsname, reprs(self._id),
                serializer.saves(event_types_py),
                serializer.saves(known_event_types_py))
        self._session._exec(cmd)
        
        # Init HasEvents, but delay initialization of handlers
        # We init after producing the JS command to create the corresponding
        # object, so that subsequent commands work ok
        super().__init__(_init_handlers=False, **kwargs)
        
        # Make JS-side events known
        for name in known_event_types_js:
            self._HasEvents__handlers.setdefault(name, [])
        
        # Initialize the model further, e.g. Widgets can create
        # subwidgets etc. This is done here, at the point where the
        # properties are initialized, but the handlers not yet.
        with self:
            self.init(*init_args)
        self._session._exec('flexx.instances.%s.init();' % self._id)
        
        # Initialize handlers for Python and for JS. Done after init()
        # so that they can connect to newly created sub Models.
        self._init_handlers()
        self._session._exec('flexx.instances.%s._init_handlers();' % self._id)
        self._session.keep_alive(self)
    
    def __repr__(self):
        clsname = self.__class__.__name__
        return "<%s object '%s' at 0x%x>" % (clsname, self._id, id(self))
    
    def __json__(self):
        return {'__type__': 'Flexx-Model',
                'session_id': self.session.id,
                'id': self.id}
    
    @staticmethod
    def __from_json__(dct):
        session = manager.get_session_by_id(dct['session_id'])
        return session.get_model_instance_by_id(dct['id'])
    
    def __enter__(self):
        # Note that __exit__ is guaranteed to be called, so there is
        # no need to use weak refs for items stored in active_models
        active_models = _get_active_models()
        active_models.append(self)
        call_later(0, self.__check_not_active)
        return self
    
    def __exit__(self, type, value, traceback):
        active_models = _get_active_models()
        assert self is active_models.pop(-1)
    
    def init(self):
        """ Can be overloaded when creating a custom class to do
        initialization, such as creating sub models. This function is
        called with this object as a context manager (the default
        context is a stub).
        """
        pass
    
    def __check_not_active(self):
        active_models = _get_active_models()
        if self in active_models:
            raise RuntimeError('It seems that the event loop is processing '
                               'events while a Model is active. This has a '
                               'high risk on race conditions.')
    
    def dispose(self):
        """ Overloaded version of dispose() that removes the global
        reference of the JS version of the object.
        """
        if self.session.status:
            try:
                self.call_js('dispose()')
            except Exception:
                pass  # ws can be closed/gone if this gets invoked from __del__
        super().dispose()
    
    @property
    def id(self):
        """ The unique id of this Model instance. """
        return self._id
    
    @property
    def session(self):
        """ The session object that connects us to the runtime.
        """
        return self._session
    
    @event.prop
    def sync_props(self, v=True):
        """ Whether properties are synchronised from JS to Python. This
        can be set to ``False`` if a model has properties that change
        a lot, but are not of interest for the Python side. Note that
        events are still synchronised if there is a Python handler.
        """
        # Use a direct approach to avoid event system here
        v = bool(v)
        self.call_js('_sync_props = true' if v else '_sync_props = false')
        return v
    
    def __setattr__(self, name, value):
        # Sync attributes that are Model instances, and not properties.
        # This is mostly intended for attributes set during init() but works
        # at any time.
        event.HasEvents.__setattr__(self, name, value)
        if isinstance(value, Model):
            if not (name in self.__properties__ or
                    (name.endswith('_value') and name[1:-6] in self.__properties__)):
                txt = serializer.saves(value)
                cmd = 'flexx.instances.%s.%s = flexx.serializer.loads(%s);' % (
                    self._id, name, reprs(txt))
                self._session._exec(cmd)
    
    def _set_prop_from_js(self, name, text):
        value = serializer.loads(text)
        #self._set_prop(name, value, True)
        if not self.__pending_props_from_js:
            call_later(0.01, self.__set_prop_from_js_pending)
        self.__pending_props_from_js.append((name, value))
    
    def __set_prop_from_js_pending(self):
        # Collect near-simultaneous prop settings in one handler call,
        # see __emit_from_js_pending
        pending, self.__pending_props_from_js = self.__pending_props_from_js, []
        for name, value in pending:
            self._set_prop(name, value, False, True)
    
    def _set_prop(self, name, value, _initial=False, fromjs=False):
        # This method differs from the JS version in that we *do
        # not* sync to JS when the setting originated from JS; this
        # is our eventual synchronicity. Python is the "end point".
        islocal = name in self.__local_properties__
        issyncable = not _initial and not islocal
        
        logger.debug('Setting prop %r on %s, fromjs=%s' % (name, self.id, fromjs))
        ischanged = super()._set_prop(name, value, _initial)
        
        if ischanged and issyncable and not fromjs:
            value = getattr(self, name)  # use normalized value
            txt = serializer.saves(value)
            cmd = 'flexx.instances.%s._set_prop_from_py(%s, %s);' % (
                self._id, reprs(name), reprs(txt))
            self._session._exec(cmd)
    
    def _register_handler(self, *args):
        event_type = args[0].split(':')[0]
        if not self.get_event_handlers(event_type):
            self.call_js('_new_event_type_hook("%s")' % event_type)
        return super()._register_handler(*args)
    
    def _handlers_changed_hook(self):
        handlers = self._HasEvents__handlers
        types = [name for name in handlers.keys() if handlers[name]]
        txt = serializer.saves(types)
        cmd = 'flexx.instances.%s._set_event_types_py(%s);' % (self._id, txt)
        self._session._exec(cmd)
    
    def _set_event_types_js(self, text):
        # Called from session.py
        self.__event_types_js = serializer.loads(text)
    
    def _emit_from_js(self, type, text):
        ev = serializer.loads(text)
        if not self.__pending_events_from_js:
            call_later(0.01, self.__emit_from_js_pending)
        self.__pending_events_from_js.append((type, ev))
    
    def __emit_from_js_pending(self):
        # Tornado uses one new tornado-event to sends one JS event.
        # This little mechanism is to collect JS events that were send
        # together, so that we can make use of our ability to
        # collectively handling events.
        pending, self.__pending_events_from_js = self.__pending_events_from_js, []
        for type, ev in pending:
            self.emit(type, ev, True)
    
    def emit(self, type, info=None, fromjs=False):
        ev = super().emit(type, info)
        isprop = type in self.__properties__ and type not in self.__local_properties__
        if not fromjs and not isprop and type in self.__event_types_js:
            cmd = 'flexx.instances.%s._emit_from_py(%s, %r);' % (
                self._id, serializer.saves(type), serializer.saves(ev))
            self._session._exec(cmd)
    
    def call_js(self, call):
        # Not documented; not sure if we keep it. Handy for debugging though
        cmd = 'flexx.instances.%s.%s;' % (self._id, call)
        self._session._exec(cmd)
    
    def send_data(self, data, meta=None):
        """ Send data to the JS side, where ``retreive_data()`` will be called,
        which will eventually call ``receive_data()`` with the corresponding
        data and meta data.
        
        AJAX is used to retrieve the data. In the future we may want to use
        a dedicated binary websocket for better performance.
        
        Parameters:
            data (bytes, str): the data blob. Can also be a URL (a string
                starting with "http://", "https://", "/flexx/data/" or "_data/")
                where the client can download the data from.
            meta (dict, optional): information associated with the data
                that the JS side can use to interpret the data. This function
                will add an "id" field to the meta data.
        """
        # Note that when send_data() is used from the init(), on the JS side
        # retrieve_data() is called before init(), unless we use call-later.
        # However, I've found that data is loaded much slower (or later) if
        # we delay the send_data call, probably because the browser can 
        # start loading the data asynchronously.
        meta = {} if meta is None else meta
        # call_later(0, self.session._send_data, self.id, data, meta)
        return self.session._send_data(self.id, data, meta)
    
    class JS:
        
        def __json__(self):
            return {'__type__': 'Flexx-Model',
                    'id': self.id,
                    'session_id': window.flexx.session_id}
        
        def __from_json__(dct):
            return window.flexx.instances[dct.id]  # one session per page, atm
        
        def __init__(self, id, py_events=None, py_known_events=None):
            
            # Set id alias. In most browsers this shows up as the first element
            # of the object, which makes it easy to identify objects while
            # debugging. This attribute should *not* be used.
            assert id
            self.__id = self._id = self.id = id
            
            self.__event_types_py = py_events if py_events else []
            
            self._sync_props = True
            
            # Init HasEvents, but delay initialization of handlers
            super().__init__(False)
            
            # Register event types that handlers can connect to without warning
            for name in py_known_events:
                self.__handlers.setdefault(name, [])
            
            # self.init() -> called from py
            # self._init_handlers() -> called from py
        
        def init(self):
            """ Can be overloaded by subclasses to initialize the model.
            """
            pass
        
        def dispose(self):
            """ Can be overloaded by subclasses to dispose resources.
            """
            window.flexx.instances[self._id] = 'disposed'
        
        def _register_handler(self, *args):
            event_type = args[0].split(':')[0]
            if not self.get_event_handlers(event_type):
                self._new_event_type_hook(event_type)
            return super()._register_handler(*args)
        
        def _new_event_type_hook(self, event_type):
            """ Called when a new event is registered.
            """
            pass
        
        def _set_prop_from_py(self, name, text):
            value = serializer.loads(text)
            self._set_prop(name, value, False, True)
        
        def _set_prop(self, name, value, _initial=False, frompy=False):
            
            # Note: there is quite a bit of _pyfunc_truthy in the ifs here
            
            islocal = self.__local_properties__.indexOf(name) >= 0
            issyncable = not _initial and not islocal and self._sync_props
            
            if window.flexx.ws is None:  # Exported app
                super()._set_prop(name, value, _initial)
                return
            
            ischanged = super()._set_prop(name, value, _initial)
            
            if ischanged and issyncable:
                value = self[name]
                txt = serializer.saves(value)
                window.flexx.ws.send('SET_PROP ' + [self.id, name, txt].join(' '))
        
        def _handlers_changed_hook(self):
            handlers = self.__handlers
            types = [name for name in handlers.keys() if len(handlers[name])]
            text = serializer.saves(types)
            if window.flexx.ws:
                window.flexx.ws.send('SET_EVENT_TYPES ' + [self.id, text].join(' '))
        
        def _set_event_types_py(self, event_types):
            self.__event_types_py = event_types
        
        def _emit_from_py(self, type, text):
            ev = serializer.loads(text)
            self.emit(type, ev, True)
        
        def emit(self, type, info=None, frompy=False):
            ev = super().emit(type, info)
            isprop = (self.__properties__.indexOf(type) >= 0 and
                      self.__local_properties__.indexOf(type) < 0 and
                      self._sync_props)
            
            if not frompy and not isprop and type in self.__event_types_py:
                txt = serializer.saves(ev)
                if window.flexx.ws:
                    window.flexx.ws.send('EVENT ' + [self.id, type, txt].join(' '))
        
        def retrieve_data(self, url, meta):
            """ Make an AJAX call to retrieve a blob of data. When the
            data is received, receive_data() is called.
            """
            # Define handler
            # print('retrieving data for', self.id, 'from', url)
            def process_response():
                if xhr.status == 200:
                    self.receive_data(xhr.response, meta)
                else:
                    raise RuntimeError("Retrieving data for %s failed with "
                                       "HTTP status %s" % (self.id, xhr.status))
            # Make AJAX call
            xhr = window.XMLHttpRequest()
            xhr.open("GET", url)
            xhr.responseType = "arraybuffer"
            xhr.onload = process_response
            xhr.send()
        
        def receive_data(self, data, meta):
            """ Function that gets called when data is send to it. Models that
            want to receive data must overload this in order to process the
            received data. The ``data`` is an ``ArrayBuffer``, and ``meta`` is
            a ``dict`` as given in ``send_data()``.
            """
            print(self.id, 'received data but did not handle it')


# Make model objects de-serializable
serializer.add_reviver('Flexx-Model', Model.__from_json__)
