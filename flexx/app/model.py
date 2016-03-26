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
from ..event._emitters import Property
from ..event._js import create_js_hasevents_class, HasEventsJS
from ..pyscript import py2js, js_rename, window

from .serialize import serializer

reprs = json.dumps


def get_model_classes():
    """ Get a list of all known Model subclasses.
    """
    return [c for c in ModelMeta.CLASSES if issubclass(c, Model)]


def get_instance_by_id(id):
    """ Get instance of Model class corresponding to the given id,
    or None if it does not exist.
    """
    return Model._instances.get(id, None)


def stub_prop_func(self, v=None):
    return v


class ModelMeta(HasEventsMeta):
    """ Meta class for Model
    Set up proxy properties in Py/JS.
    """
    
    # Keep track of all subclasses
    CLASSES = []
    
    def __init__(cls, name, bases, dct):
        HasEventsMeta.__init__(cls, name, bases, dct)
        
        ModelMeta.CLASSES.append(cls)
        
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
                        setattr(JS, name, val)
                    elif name in OK_MAGICS:
                        setattr(JS, name, val)
        
        # Finalize the JS class (e.g. need this to convert on_xxx)
        cls.JS = finalize_hasevents_class(JS)
        
        # Init proxy props
        JS.__proxy_properties__ = list(getattr(JS, '__proxy_properties__', []))
        cls.__proxy_properties__ = list(getattr(cls, '__proxy_properties__', []))
        
        # Create proxy properties on cls for each property on JS
        if 'JS' in cls.__dict__:
            for name, val in cls.JS.__dict__.items():
                if isinstance(val, Property):
                    if name in JS.__proxy_properties__ or name in cls.__proxy_properties__:
                        pass  # This is a proxy, or we already have a proxy for it
                    elif not hasattr(cls, name):
                        cls.__proxy_properties__.append(name)
                        p = Property(stub_prop_func, name, val._func.__doc__)
                        setattr(cls, name, p)
                    else:
                        logging.warn('JS property %r not proxied on %s, '
                                     'as it would hide a Py attribute.' % (name, cls.__name__))
        
        # Create proxy properties on cls.JS for each property on cls
        for name, val in cls.__dict__.items():
            if isinstance(val, Property):
                if name in JS.__proxy_properties__ or name in cls.__proxy_properties__:
                    pass  # This is a proxy, or we already have a proxy for it
                elif not hasattr(cls.JS, name):
                    # todo: readonlies?
                    JS.__proxy_properties__.append(name)
                    p = Property(stub_prop_func, name, val._func.__doc__)
                    setattr(cls.JS, name, p)
                else:
                    logging.warn('Py property %r not proxied on %s, '
                                 'as it would hide a JS attribute.' % (name, cls.__name__))
        
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
            code.append('flexx.serializer = new flexx.Serializer();')
            c = js_rename(HasEventsJS.JSCODE, 'HasEvents', 'flexx.classes.HasEvents')
            code.append(c)
        # Add this class
        code.append(create_js_hasevents_class(cls.JS, cls_name, base_class))
        # todo: class name handle at pyscript level?
        code[-1] += '%s.prototype._class_name = "%s";\n' % (cls_name, cls.__name__)
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
        
        # Instantiate JavaScript version of this class
        clsname = 'flexx.classes.' + self.__class__.__name__
        cmd = 'flexx.instances.%s = new %s(%s);' % (self._id, clsname, reprs(self._id))
        self._session._exec(cmd)
        
        self._init()
        super().__init__(**kwargs)
    
    def _init(self):
        """ Can be overloaded when creating a custom class.
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
    
    def __setattr__(self, name, value):
        # Sync attributes that are Model instances
        event.HasEvents.__setattr__(self, name, value)
        if isinstance(value, Model):
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
        
        if fromjs or not isproxy:  # Only not set if isproxy and not from js
            super()._set_prop(name, value)
        
        if not (fromjs and isproxy):  # only not send if fromjs and isproxy
            if not isproxy:  # if not a proxy, use normalized value
                value = getattr(self, name)
            txt = serializer.saves(value)
            cmd = 'flexx.instances.%s._set_prop_from_py(%s, %s);' % (
                self._id, reprs(name), reprs(txt))
            self._session._exec(cmd)
    
    def _init_prop(self, name):
        isproxy = name in self.__proxy_properties__
        if not isproxy:
            super()._init_prop(name)
            value = getattr(self, name)
            txt = serializer.saves(value)
            cmd = 'flexx.instances.%s._set_prop_from_py(%s, %s);' % (
                self._id, reprs(name), reprs(txt))
            self._session._exec(cmd)
    
    def _link_js_signal(self, name, link=True):
        """ Make a link between a JS signal and its proxy in Python.
        This is done when a proxy signal is used as input for a signal
        in Python.
        """
        # if self._session is None:
        #     self._initial_signal_links.discart(name)
        #     if link:
        #         self._initial_signal_links.add(name)
        # else:
        link = 'true' if link else 'false'
        cmd = 'flexx.instances.%s._link_js_signal(%s, %s);' % (self._id,
                                                               reprs(name), link)
        self._session._exec(cmd)
    
    def call_js(self, call):
        cmd = 'flexx.instances.%s.%s;' % (self._id, call)
        self._session._exec(cmd)
    
    
    class JS:
        
        def __json__(self):
            return {'__type__': 'Flexx-Model', 'id': self.id}
        
        def __from_json__(dct):
            return window.flexx.instances[dct.id]
        
        def __init__(self, id):
            # Set id alias. In most browsers this shows up as the first element
            # of the object, which makes it easy to identify objects while
            # debugging. This attribute should *not* be used.
            self.__id = self._id = self.id = id
            
            self._linked_signals = {}  # use a list as a set
            
            # Call _init now. This gives subclasses a chance to init at a time
            # when the id is set, but *before* the handlers are connected.
            self._init()
            
            # Call HasEvents __init__, properties will be created and connected.
            super().__init__()
        
        def _init(self):
            pass
        
        def _set_prop_from_py(self, name, text):
            value = window.flexx.serializer.loads(text)
            self._set_prop(name, value, True)
        
        def _set_prop(self, name, value, frompy=False):
            isproxy = self.__proxy_properties__.indexOf(name) >= 0
            
            if window.flexx.ws is None:
                # Exported or in an nbviewer;
                # assume the value needs no checking or normalization
                return super()._set_prop(name, value)
            
            if frompy or not isproxy:  # Only not set if isproxy and not frompy
                super()._set_prop(name, value)
            
            if not (frompy and isproxy):  # only not send if frompy and isproxy
                if not isproxy:  # if not a proxy, use normalized value
                    value = self[name]
                txt = window.flexx.serializer.saves(value)
                window.flexx.ws.send('SETPROP ' + [self.id, name, txt].join(' '))
        
        def _init_prop(self, name):
            isproxy = self.__proxy_properties__.indexOf(name) >= 0
            if not isproxy:
                super()._init_prop(name)
                value = self[name]
                txt = window.flexx.serializer.saves(value)
                window.flexx.ws.send('SETPROP ' + [self.id, name, txt].join(' '))
        
        def _link_js_signal(self, name, link):
            if link:
                self._linked_signals[name] = True
                signal = self[name]
                if signal._timestamp > 1:
                    self._signal_changed(self[name])
            elif self._linked_signals[name]:
                del self._linked_signals[name]

# Make model objects de-serializable
serializer.add_reviver('Flexx-Model', Model.__from_json__)
