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

import json
import weakref
import threading

from .. import event
from ..event._hasevents import (with_metaclass, new_type, HasEventsMeta,
                                finalize_hasevents_class)
from ..event._emitters import Emitter
from ..event._js import create_js_hasevents_class, HasEventsJS
from ..pyscript import py2js, js_rename, window, Parser

from .serialize import serializer
from . import logger

reprs = json.dumps

call_later = None  # reset in func.py to deal with circular dependency


def get_model_classes():
    """ Get a list of all known Model subclasses.
    """
    return [c for c in ModelMeta.CLASSES if issubclass(c, Model)]


def get_instance_by_id(id):
    """ Get instance of Model class corresponding to the given id,
    or None if it does not exist.
    """
    try:
        return Model._instances[id]
    except KeyError:
        logger.warn('Model instance %r does not exist in Python (anymore).' % id)
        return None  # Could we revive it? ... probably not a good idea


# Keep track of a stack of "active" models for use within context
# managers. We have one list for each thread. Note that we should limit
# its use to context managers, and execution should never be handed back
# to the Tornado event loop while inside a context.
_active_models_per_thread = {}  # dict of threadid -> list

def _get_active_models():
    """ Get list that represents the stack of "active" models.
    Each thread has its own stack. Should only be used inside a Model
    context manager.
    """
    # Get thread id
    if hasattr(threading, 'current_thread'):
        tid = id(threading.current_thread())
    else:  # pragma: no cover
        tid = id(threading.currentThread())
    # Get list of parents for this thread
    return _active_models_per_thread.setdefault(tid, [])


def get_active_model():
    """ If the execution is now in a Model context manager, return the
    corresponding object, and None otherwise. Can be used by subclasses
    to implement parenting-like behaviour using the with-statement.
    """
    models = _get_active_models()
    if models:
        return models[-1]


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
        Parser.NAME_MAP[cls_name] = 'flexx.classes.%s' % cls_name
        
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
        
        # Copy properties from Both class to main class and JS class
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
        
        # Set JS and CSS for this class
        cls.JS.CODE = cls._get_js()
        cls.CSS = cls.__dict__.get('CSS', '')
    
    def _get_js(cls):
        """ Get source code for this class.
        """
        cls_name = 'flexx.classes.' + cls.__name__
        base_class = 'flexx.classes.%s.prototype' % cls.mro()[1].__name__
        code = []
        # Add JS version of HasEvents when this is the Model class
        if cls.mro()[1] is event.HasEvents:
            c = py2js(serializer.__class__, 'flexx.Serializer', inline_stdlib=False)
            code.append(c)
            code.append('flexx.serializer = new flexx.Serializer();\n\n')
            c = js_rename(HasEventsJS.JSCODE, 'HasEvents', 'flexx.classes.HasEvents')
            code.append(c)
        # Add this class
        code.append(create_js_hasevents_class(cls.JS, cls_name, base_class))
        if cls.mro()[1] is event.HasEvents:
            code.append('flexx.serializer.add_reviver("Flexx-Model",'
                        ' flexx.classes.Model.prototype.__from_json__);\n')
        return '\n'.join(code)



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
    
    # Keep track of all instances, so we can easily collect al JS/CSS
    _instances = weakref.WeakValueDictionary()
    
    # Count instances to give each instance a unique id
    _counter = 0
    
    # CSS for this class (no css in the base class)
    CSS = ""
    
    def __init__(self, session=None, is_app=False, **kwargs):
        
        # Param "is_app" is not used, but we "take" the argument so it
        # is not mistaken for a property value.
        
        # Set id and register this instance
        Model._counter += 1
        self._id = self.__class__.__name__ + str(Model._counter)
        Model._instances[self._id] = self
        
        # Init session
        if session is None:
            active_model = get_active_model()
            if active_model is not None:
                session = active_model.session
        if session is None:
            from .session import manager
            session = manager.get_default_session()
        if session is None:
            raise RuntimeError('Cannot instantiate Model %r without a session'
                               % self.id)
        self._session = session
        self._session.register_model_class(self.__class__)
        
        # Get initial event connections
        event_types_py, event_types_js = [], []
        for handler_name in self.__handlers__:
            descriptor = getattr(self.__class__, handler_name)
            event_types_py.extend(descriptor.local_connection_strings)
        for handler_name in self.JS.__handlers__:
            descriptor = getattr(self.JS, handler_name)
            event_types_js.extend(descriptor.local_connection_strings)
        
        # Further initialization of attributes
        self.__event_types_js = event_types_js
        self.__pending_events_from_js = []
        self.__pending_props_from_js = []
        
        # Instantiate JavaScript version of this class
        clsname = 'flexx.classes.' + self.__class__.__name__
        cmd = 'flexx.instances.%s = new %s(%s, %s);' % (
                self._id, clsname, reprs(self._id), serializer.saves(event_types_py))
        self._session._exec(cmd)
        
        # Init HasEvents, but delay initialization of handlers
        # We init after producing the JS command to create the corresponding
        # object, so that subsequent commands work ok
        super().__init__(_init_handlers=False, **kwargs)
        
        # Initialize the model further, e.g. Widgets can create
        # subwidgets etc. This is done here, at the point where the
        # properties are initialized, but the handlers not yet.
        with self:
            self.init()
        self._session._exec('flexx.instances.%s.init();' % self._id)
        
        # Initialize handlers for Python and for JS. Done after init()
        # so that they can connect to newly created sub Models.
        self._init_handlers()
        self._session._exec('flexx.instances.%s._init_handlers();' % self._id)
    
    def __repr__(self):
        clsname = self.__class__.__name__
        return "<%s object '%s' at 0x%x>" % (clsname, self._id, id(self))
    
    def __json__(self):
        return {'__type__': 'Flexx-Model', 'id': self.id}
    
    @staticmethod
    def __from_json__(dct):
        return get_instance_by_id(dct['id'])
    
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
            cmd = 'flexx.instances.%s = "disposed";' % self._id
            self._session._exec(cmd)
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
    
    # todo: limit this to within init()?
    def __setattr__(self, name, value):
        # Sync attributes that are Model instances, and not properties
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
    
    def emit(self, type, ev, fromjs=False):
        ev = super().emit(type, ev)
        isprop = type in self.__properties__ and type not in self.__local_properties__
        if not fromjs and not isprop and type in self.__event_types_js:
            cmd = 'flexx.instances.%s._emit_from_py(%s, %r);' % (
                self._id, serializer.saves(type), serializer.saves(ev))
            self._session._exec(cmd)
    
    def call_js(self, call):
        # Not documented; not sure if we keep it. Handy for debugging though
        cmd = 'flexx.instances.%s.%s;' % (self._id, call)
        self._session._exec(cmd)
    
    
    class JS:
        
        def __json__(self):
            return {'__type__': 'Flexx-Model', 'id': self.id}
        
        def __from_json__(dct):
            return window.flexx.instances[dct.id]
        
        def __init__(self, id, py_events=None):
            
            # Set id alias. In most browsers this shows up as the first element
            # of the object, which makes it easy to identify objects while
            # debugging. This attribute should *not* be used.
            assert id
            self.__id = self._id = self.id = id
            
            self.__event_types_py = py_events if py_events else []
            
            self._sync_props = True
            
            # Init HasEvents, but delay initialization of handlers
            super().__init__(False)
            
            # self.init() -> called from py
            # self._init_handlers() -> called from py
        
        def init(self):
            """ Can be overloaded by subclasses to initialize the model.
            """
            pass
        
        def _set_prop_from_py(self, name, text):
            value = window.flexx.serializer.loads(text)
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
                txt = window.flexx.serializer.saves(value)
                window.flexx.ws.send('SET_PROP ' + [self.id, name, txt].join(' '))
        
        def _handlers_changed_hook(self):
            handlers = self.__handlers
            types = [name for name in handlers.keys() if len(handlers[name])]
            text = window.flexx.serializer.saves(types)
            if window.flexx.ws:
                window.flexx.ws.send('SET_EVENT_TYPES ' + [self.id, text].join(' '))
        
        def _set_event_types_py(self, event_types):
            self.__event_types_py = event_types
        
        def _emit_from_py(self, type, text):
            ev = window.flexx.serializer.loads(text)
            self.emit(type, ev, True)
        
        def emit(self, type, ev, frompy=False):
            ev = super().emit(type, ev)
            isprop = (self.__properties__.indexOf(type) >= 0 and
                      self.__local_properties__.indexOf(type) < 0 and
                      self._sync_props)
            
            if not frompy and not isprop and type in self.__event_types_py:
                txt = window.flexx.serializer.saves(ev)
                if window.flexx.ws:
                    window.flexx.ws.send('EVENT ' + [self.id, type, txt].join(' '))


# Make model objects de-serializable
serializer.add_reviver('Flexx-Model', Model.__from_json__)
