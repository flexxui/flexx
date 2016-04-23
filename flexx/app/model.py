"""
Base class for objects that live in both Python and JS.
This basically implements the syncing of properties and events.
"""

import sys
import json
import weakref
import logging

from .. import event
from ..event._hasevents import with_metaclass, new_type, HasEventsMeta, finalize_hasevents_class
from ..event._emitters import Property, Emitter
from ..event._js import create_js_hasevents_class, HasEventsJS
from ..pyscript import py2js, js_rename, window, Parser

from .serialize import serializer

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
        logging.warn('Model instance %r does not exist in Python (anymore).' % id)
        return None  # Could we revive it? ... probably not a good idea


def stub_prop_func(self, v=None):
    return v

def stub_emitter_func_py(self, *args):
    raise RuntimeError('This emitter can only be called from JavaScript')

def stub_emitter_func_js(self, *args):
    raise RuntimeError('This emitter can only be called from Python')


class ModelMeta(HasEventsMeta):
    """ Meta class for Model
    Set up proxy properties in Py/JS.
    """
    
    # Keep track of all subclasses
    CLASSES = []
    
    def __init__(cls, name, bases, dct):
        HasEventsMeta.__init__(cls, name, bases, dct)
        
        # Register this class and make PyScript convert the name
        ModelMeta.CLASSES.append(cls)
        Parser.NAME_MAP[name] = 'flexx.classes.%s' % name
        
        OK_MAGICS = '__init__', '__json__', '__from_json__'
        
        # Implicit inheritance for JS "sub"-class
        jsbases = [getattr(b, 'JS') for b in cls.__bases__ if hasattr(b, 'JS')]
        JS = new_type('JS', tuple(jsbases), {})
        for c in (cls, ):  # cls.__bases__ + (cls, ):
            if 'JS' in c.__dict__:
                if '__init__' in c.JS.__dict__:
                    JS.__init__ = c.JS.__init__
                for name, val in c.JS.__dict__.items():
                    if not name.startswith('__'):
                        bettername = name.replace('_JS__', '_' + c.__name__ + '__')
                        setattr(JS, bettername, val)
                    elif name in OK_MAGICS:
                        setattr(JS, name, val)
        
        # Finalize the JS class (e.g. need this to convert on_xxx)
        cls.JS = finalize_hasevents_class(JS)
        
        # Init proxy props
        JS.__proxy_properties__ = list(getattr(JS, '__proxy_properties__', []))
        cls.__proxy_properties__ = list(getattr(cls, '__proxy_properties__', []))
        
        # Create proxy properties on cls for each property on JS
        for name, val in cls.JS.__dict__.items():
            if isinstance(val, Property):
                if name in JS.__proxy_properties__ or name in cls.__proxy_properties__:
                    pass  # This is a proxy, or we already have a proxy for it
                elif val._flags.get('both', False):
                    raise RuntimeError("Prop %r with flag 'both' should not be "
                                       "defined on JS class." % name)
                elif not val._flags.get('sync', True):
                    pass  # prop that should not be synced
                elif not hasattr(cls, name):
                    cls.__proxy_properties__.append(name)
                    p = val.__class__(stub_prop_func, name, val._func.__doc__)
                    setattr(cls, name, p)
                else:
                    logging.warn('JS property %r not proxied on %s, '
                                    'as it would hide a Py attribute.' % (name, cls.__name__))
            elif isinstance(val, Emitter) and not hasattr(cls, name):
                p = val.__class__(stub_emitter_func_py, name, val._func.__doc__)
                setattr(cls, name, p)
        
        # Create proxy properties on cls.JS for each property on cls
        for name, val in cls.__dict__.items():
            if isinstance(val, Property):
                if name in JS.__proxy_properties__ or name in cls.__proxy_properties__:
                    pass  # This is a proxy, or we already have a proxy for it
                elif val._flags.get('both', False):
                    setattr(cls.JS, name, val)  # copy the property
                    cls.JS.__properties__.append(name)
                elif not val._flags.get('sync', True):
                    pass  # prop that should not be synced
                elif not hasattr(cls.JS, name):
                    JS.__proxy_properties__.append(name)
                    p = val.__class__(stub_prop_func, name, val._func.__doc__)
                    setattr(cls.JS, name, p)
                else:
                    logging.warn('Py property %r not proxied on %s, '
                                 'as it would hide a JS attribute.' % (name, cls.__name__))
            elif isinstance(val, Emitter) and not hasattr(cls, name):
                p = val.__class__(stub_emitter_func_js, name, val._func.__doc__)
                setattr(cls, name, p)
        
        # Finalize classes to update __properties__ (we may have added some)
        finalize_hasevents_class(cls)
        finalize_hasevents_class(JS)
        # Finish proxy lists
        cls.__proxy_properties__.sort()
        JS.__proxy_properties__.sort()
        
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
    """ Subclass of HasEvents representing Python-JavaScript object models
    
    Each instance of this class has a corresponding object in
    JavaScript. Properties are present on both sides, and events are
    transparently handled accross the language barrier.
    
    The JS version of this class is defined by the contained ``JS``
    class. One can define methods, properties, handlers, and (json
    serializable) constants on the JS class.
    
    Parameters:
        session (Session, None): the session object that connects this
            instance to a JS client.
        is_app (bool): whether this object is the main app object. Set
            by Flexx internally. Not used by the Model class, but can
            be used by subclasses.
        kwargs: initial property values (see HasEvents).
    
    Notes:
        This class provides the base object for all widget classes in
        ``flexx.ui``. However, one can also create subclasses that have
        nothing to do with user interfaces or DOM elements. You could e.g.
        use it to calculate pi on nodejs.
    
    Example:
    
        .. code-block:: py
        
            class MyModel(Model):
                
                def a_python_method(self):
                ...
                
                class JS:
                    
                    FOO = [1, 2, 3]
                    
                    def a_js_method(this):
                        ...
    """
    
    # Keep track of all instances, so we can easily collect al JS/CSS
    _instances = weakref.WeakValueDictionary()
    
    # Count instances to give each instance a unique id
    _counter = 0
    
    # CSS for this class (no css in the base class)
    CSS = ""
    
    def __json__(self):
        return {'__type__': 'Flexx-Model', 'id': self.id}
    
    @staticmethod
    def __from_json__(dct):
        return get_instance_by_id(dct['id'])
    
    def __init__(self, session=None, is_app=False, **kwargs):
        
        # Init HasEvents, but delay initialization of handlers
        super().__init__(_init_handlers=False, **kwargs)
        
        # Param "is_app" is not used, but we "take" the argument so it
        # is not mistaken for a property value.
        
        # Set id and register this instance
        Model._counter += 1
        self._id = self.__class__.__name__ + str(Model._counter)
        Model._instances[self._id] = self
        
        # Init session
        if session is None:
            from .session import manager
            session = manager.get_default_session()
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
        
        # Instantiate JavaScript version of this class
        clsname = 'flexx.classes.' + self.__class__.__name__
        cmd = 'flexx.instances.%s = new %s(%s, %s);' % (
                self._id, clsname, reprs(self._id), serializer.saves(event_types_py))
        self._session._exec(cmd)
        
        # Initialize the model further, e.g. Widgets can create
        # subwidgets etc. This is done here, at the point where the
        # properties are initialized, but the handlers not yet. Handlers
        # are initialized after this, so that they can connect to newly
        # created sub Models. This class implements a stub contect manager.
        with self:
            self.init()
        
        # Finish initialization, here and in JS. Important to schedule
        # JS before we init ourselves, because of prop initialization.
        cmd = 'flexx.instances.%s._init_handlers();' % self._id
        self._session._exec(cmd)
        self._init_handlers()
    
    def __enter__(self):
        pass
    
    def __exit__(self, type, value, traceback):
        pass
        
    def __repr__(self):
        clsname = self.__class__.__name__
        return "<%s object '%s' at 0x%x>" % (clsname, self._id, id(self))
    
    def dispose(self):
        """ Overloaded version of dispose() that removes the global
        reference of the JS version of the object.
        """
        if self.session.status:
            cmd = 'flexx.instances.%s = "disposed";' % self._id
            self._session._exec(cmd)
        super().dispose()
    
    def init(self):
        """ Can be overloaded when creating a custom class to do
        initialization, such as creating sub models. This function is
        called with this object as a context manager (the default
        context is a stub).
        """
        pass
    
    @property
    def id(self):
        """ The unique id of this Model instance. """
        return self._id
    
    @property
    def session(self):
        """ The session object that connects us to the runtime.
        """
        return self._session
    
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
        """ Notes on synchronizing:
        Properties are synced, following the principle of eventual
        synchronicity (props may become out of sync, but should become
        equal after a certain time). The side on which the property is defined
        functions as the reference+
        """
        value = serializer.loads(text)
        self._set_prop(name, value, True)
    
    def _set_prop(self, name, value, fromjs=False):
        isproxy = name in self.__proxy_properties__
        shouldsend = self.__emitter_flags__[name].get('sync', True)
        
        if fromjs or not isproxy:  # Only not set if isproxy and not from js
            shouldsend = super()._set_prop(name, value) and shouldsend
        
        if shouldsend and not (fromjs and isproxy):  # only not send if fromjs and isproxy
            if not isproxy:  # if not a proxy, use normalized value
                value = getattr(self, name)
            txt = serializer.saves(value)
            cmd = 'flexx.instances.%s._set_prop_from_py(%s, %s);' % (
                self._id, reprs(name), reprs(txt))
            self._session._exec(cmd)
    
    def _init_prop(self, name):
        isproxy = name in self.__proxy_properties__
        isboth = self.__emitter_flags__[name].get('both', False)
        shouldsend = self.__emitter_flags__[name].get('sync', True)
        
        super()._init_prop(name)
        
        if shouldsend and not (isproxy or isboth):
            super()._init_prop(name)
            value = getattr(self, name)
            txt = serializer.saves(value)
            cmd = 'flexx.instances.%s._set_prop_from_py(%s, %s);' % (
                self._id, reprs(name), reprs(txt))
            self._session._exec(cmd)
    
    def _handlers_changed_hook(self):
        types = [name for name in self._he_handlers.keys() if self._he_handlers[name]]
        cmd = 'flexx.instances.%s._set_event_types_py(%s);' % (self._id, serializer.saves(types))
        self._session._exec(cmd)
    
    def _set_event_types_js(self, text):
        # Called from session.py
        self.__event_types_js = serializer.loads(text)
    
    def _emit_from_js(self, type, text):
        ev = serializer.loads(text)
        if not self.__pending_events_from_js:
            call_later(0.01, self.__emit_pending_from_js)
        self.__pending_events_from_js.append((type, ev))
    
    def __emit_pending_from_js(self):
        # Tornado uses one new tornado-event to sends one JS event.
        # This little mechanism is to collect JS events that were send
        # together, so that we can make use of our ability to
        # collectively handling events.
        pending, self.__pending_events_from_js = self.__pending_events_from_js, []
        for type, ev in pending:
            self.emit(type, ev, True)
    
    def emit(self, type, ev, fromjs=False):
        ev = super().emit(type, ev)
        isprop = type in self.__properties__  # are emitted via their proxies
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
            
            # Init HasEvents, but delay initialization of handlers
            super().__init__(False)
            
            # Set id alias. In most browsers this shows up as the first element
            # of the object, which makes it easy to identify objects while
            # debugging. This attribute should *not* be used.
            assert id
            self.__id = self._id = self.id = id
            
            self.__event_types_py = py_events if py_events else []
            
            # Initialize when properties are initialized, but before handlers
            # are initialized. These are initialized by a call from Python.
            self.init()
        
        def init(self):
            """ Can be overloaded by subclasses to initialize the model.
            """
            pass
        
        def _set_prop_from_py(self, name, text):
            value = window.flexx.serializer.loads(text)
            self._set_prop(name, value, True)
        
        def _set_prop(self, name, value, frompy=False):
            # This method differs from the Python version in that
            # we *do not* sync to Py when the setting originated from py and
            # it is a "both" property; this is our eventual synchronicity.
            
            isproxy = self.__proxy_properties__.indexOf(name) >= 0
            isboth = self.__emitter_flags__[name].get('both', False)
            shouldsend = self.__emitter_flags__[name].get('sync', True)
            
            # Note: there is quite a bit of _pyfunc_truthy in the ifs here
            if window.flexx.ws is None:
                if not isproxy:
                    super()._set_prop(name, value)
                else:
                    window.console.warn("Cannot set prop '%s' because its validated "
                                        "in Py, but there is no websocket." % name)
                return
            
            if frompy or not isproxy:  # Only not set if isproxy and not frompy
                shouldsend = super()._set_prop(name, value) and shouldsend
            
            if shouldsend and not (frompy and (isproxy or isboth)):
                if not isproxy:  # if not a proxy, use normalized value
                    value = self[name]
                txt = window.flexx.serializer.saves(value)
                window.flexx.ws.send('SET_PROP ' + [self.id, name, txt].join(' '))
        
        def _init_prop(self, name):
            isproxy = self.__proxy_properties__.indexOf(name) >= 0
            isboth = self.__emitter_flags__[name].get('both', False)
            shouldsend = self.__emitter_flags__[name].get('sync', True)
            
            super()._init_prop(name)
            
            if shouldsend and not (isproxy or isboth):
                value = self[name]
                txt = window.flexx.serializer.saves(value)
                if window.flexx.ws:
                    window.flexx.ws.send('SET_PROP ' + [self.id, name, txt].join(' '))
        
        def _handlers_changed_hook(self):
            types = [name for name in self._he_handlers.keys() if len(self._he_handlers[name])]
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
            isprop = self.__properties__.indexOf(type) >= 0
            
            if not frompy and not isprop and type in self.__event_types_py:
                txt = window.flexx.serializer.saves(ev)
                if window.flexx.ws:
                    window.flexx.ws.send('EVENT ' + [self.id, type, txt].join(' '))


# Make model objects de-serializable
serializer.add_reviver('Flexx-Model', Model.__from_json__)
