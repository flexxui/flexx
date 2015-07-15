""" Base class for objects that live in both Python and JS

This basically implements the syncing of signals.
"""

import sys
import json
import weakref
import hashlib

from ...react import react
from ...react.pyscript import create_js_signals_class, HasSignalsJS

from ...pyscript import js, JSCode
from ...pyscript.parser2 import get_class_definition

if sys.version_info[0] >= 3:
    string_types = str,
else:
    string_types = basestring,


paired_classes = []
def get_mirrored_classes(): # todo: rename to paired
    """ Get a list of all known Mirrored subclasses.
    """
    return [c for c in HasSignalsMeta.CLASSES if issubclass(c, Paired)]


def get_instance_by_id(id):
    """ Get instance of Mirrored class corresponding to the given id,
    or None if it does not exist.
    """
    return Paired._instances.get(id, None)


import json

class JSSignal(react.SourceSignal):
    """ A signal that represents a proxy to a signal in JavaScript.
    """
    
    def __init__(self, name_or_func, upstream=[], *args, **kwargs):
        assert not upstream
        
        def func(v=''):
            return json.loads(v)
        
        name = name_or_func if isinstance(name_or_func, string_types) else func.__name__
        func.__name__ = name
        
        react.SourceSignal.__init__(self, func, [], *args, **kwargs)


class PySignal(react.SourceSignal):
    """ A signal in JS that represents a proxy to a signal in Python.
    """
    
    def __init__(self, name):
        
        def func(v=None):
            return json.dumps(v)
        
        react.SourceSignal.__init__(self, func, [])
        self._name = name


class PairedMeta(react.HasSignalsMeta):
    """ Meta class for Paired
    Set up proxy signals in Py/JS.
    """
 
    def __init__(cls, name, bases, dct):
        react.HasSignalsMeta.__init__(cls, name, bases, dct)
        
        # Create proxy signals on cls for each signal on JS
        if 'JS' in cls.__dict__:
            for name, val in cls.JS.__dict__.items():
                if isinstance(val, react.Signal) and not isinstance(val, PySignal):
                    if not hasattr(cls, name):
                        cls.__signals__.append(name)
                        setattr(cls, name, JSSignal(name))
                    elif isinstance(getattr(cls, name), JSSignal):
                        pass  # ok, overloaded signal on JS side
                    else:
                        print('Warning: JS signal %r not proxied, as it would hide a Py attribute.' % name)
        
        # Implicit inheritance for JS "sub"-class
        JS = type('JS', (object, ), {})
        for c in cls.__bases__ + (cls, ):
            if 'JS' in c.__dict__:
                JS.__init__ = c.__init__
                for name, val in c.JS.__dict__.items():
                    if not name.startswith('__'):
                        if hasattr(JS, name):  # todo: remove this (leaving now to prevent breaking it)
                            print('Warning: %s.JS already has %r' % (cls, name))
                        setattr(JS, name, val)
        cls.JS = JS
        
        # Create proxy signals on cls.JS for each signal on cls
        for name, val in cls.__dict__.items():
            if isinstance(val, react.Signal) and not isinstance(val, JSSignal):
                if not hasattr(cls.JS, name):
                    setattr(cls.JS, name, PySignal(name))
                elif isinstance(getattr(cls.JS, name), PySignal):
                    pass  # ok, overloaded signal on JS side
                else:
                    print('Warning: Py signal %r not proxied, as it would hide a JS attribute.' % name)


class Paired(react.with_metaclass(PairedMeta, react.HasSignals)):
    """ Class for which objects exist both in Python and JS. 
    
    Each instance of this class has a mirror object in JavaScript, and
    their signals are synced both ways. Methods can be defined than
    can be either executed in Python or in JavaScript (by decorating
    them with ``js``).
    
    This class provides the base object for all widget classes in
    flexx.ui. However, one can also create subclasses that have nothing
    to do with user interfaces or DOM elements. You could e.g. use it
    to calculate pi on nodejs.
    
    Each instance has a unique id, which is also available in JS.
    Instances can be looked up by id via the get_instance_by_id()
    function.
    """
    
    # Keep track of all instances, so we can easily collect al JS/CSS
    _instances = weakref.WeakValueDictionary()
    
    # Count instances to give each instance a unique id
    _counter = 0
    
    # CSS for this class (no css in the base class)
    CSS = ""
    
    # Names of events
    _EVENT_NAMES = []
    
    @react.input
    def id(self, v=None):
        """ The unique id of this Paired instance """
        return self._id
    
    @react.act('id')
    def show_id(v):
        print('id is', v)
    
    def __init__(self, _proxy=None, **kwargs):
        react.HasSignals.__init__(self, **kwargs)
        
        # Associate with an app
        from .app import manager
        if _proxy is None:
            _proxy = manager.get_default_proxy()
        self._proxy = _proxy
            
        # Set id and register this instance
        Paired._counter += 1
        self._id = self.__class__.__name__ + str(Paired._counter)
        Paired._instances[self._id] = self
        
        # Instantiate JavaScript version of this class
        clsname = 'flexx.classes.' + self.__class__.__name__
        
        # props = {}
        # for name in self.props():
        #     val = getattr(self, name)
        #     props[name] = getattr(self.__class__, name).to_json(val)
        # cmd = 'flexx.instances.%s = new %s(%s);' % (self.id, clsname, json.dumps(props))
        # self._proxy._exec(cmd)
        
        # todo: get notified when a prop changes, pend a call via call_later
        # todo: collect more changed props if they come by
        # todo: in the callback send all prop updates to js
        
        # # Register callbacks
        # for name in self.props():
        #     self.add_listener(name, self._sync_prop)
    
    @property
    def proxy(self):
        """ The proxy object that connects us to the runtime.
        """
        return self._proxy
    
    def _sync_prop(self, name, old, new):
        """ Callback to sync properties to JS
        """
        # Note: the JS function _set_property is defined below
        txt = getattr(self.__class__, name).to_json(new)
        #print('sending json', txt)
        cmd = 'flexx.instances.%s._set_property(%r, %r, true, true);' % (self.id, name, txt)
        self._proxy._exec(cmd)
    
    
    class JS:
        
        def __init__(self, initial_signal_values):
            
            # Set id alias. In most browsers this shows up as the first element
            # of the object, which makes it easy to identify objects while
            # debugging. This attribute should *not* be used.
            self.__id = initial_signal_values['id']
            
            # Init events handlers
            # todo: init all events defined at the class
            self._event_handlers = {}
            for event_name in self._EVENT_NAMES:
                self._event_handlers[event_name] = []
            
            # Create properties
            for name in props:
                opts = {"enumerable": True}
                gs = self._getter_setter(name)
                opts['get'] = gs[0]
                opts['set'] = gs[1]
                Object.defineProperty(self, name, opts)
        
            # First init all property values, without calling the changed-func
            for name in props:
                self._set_property(name, props[name], True, False)
            
            # Init (with props set to their initial value)
            self._init()
            
            # Emit changed events
            for name in props:
                if self['_'+name+'_changed']:
                    self['_'+name+'_changed'](name, None, self['_'+name])
        
        def _init(self):
            pass  # Subclasses should overload this
        
        @react.source
        def stub_mouse_pos(pos=(0, 0)):
            return tuple(float(p[0]), float(p[1]))
        
        def _set_property(self, name, val, fromjson=False, emit=True):
            """ Set a property value with control over json conversion
            and calling of changed-function.
            """
            oval = val
            if fromjson:
                if self['_from_json_'+name]:  # == function 
                    val = self['_from_json_'+name](val)
                else:
                    val = JSON.parse(val)
                val = None if val is undefined else val
            old = self['_' + name]
            self['_' + name] = val
            if emit and self['_'+name+'_changed']:
                self['_'+name+'_changed'](name, old, val)
        
        def _getter_setter(name):
            # Provide scope for closures
            def getter():
                if self['_get_'+name]:
                    return self['_get_' + name]()
                else:
                    return self['_' + name]
            def setter(val):
                self._set_property(name, val, False, True)
                value = self['_' + name]
                if self['_to_json_'+name]:  # == function
                    txt = self['_to_json_'+name](value)
                else:
                    txt = JSON.stringify(value)
                if flexx.ws is not None:  # we could be exported or in an nbviewer
                    flexx.ws.send('PROP ' + self.id + ' ' + name + ' ' + txt)
            return getter, setter
        
        ## JS event system
        
        def _has_handler(self, handler, handlers):
            """ Test "handler in handlers", but work correctly if handler
            is a tuple.
            """
            if isinstance(handler, list):
                for i in range(len(handlers)):
                    h = handlers[i]
                    if handler[0] == h[0] and handler[1] == h[1]:
                        return True
                else:
                    return False
            else:
                return handler in handlers
        
        def connect_event(self, name, handler):
            if name not in self._event_handlers:
                raise ValueError('Event %s not known' % name)
            handlers = self._event_handlers[name]
            if not self._has_handler(handler, handlers):
                handlers.append(handler)
        
        def disconnect_event(self, name, handler):
            if name not in self._event_handlers:
                raise ValueError('Event %s not known' % name)
            handlers = self._event_handlers[name]
            while self._has_handler(handler, handlers):
                handlers.remove(handler)
        
        def emit_event(self, name, event):
            if name not in self._event_handlers:
                raise ValueError('Event %s not known' % name)
            handlers = self._event_handlers[name]
            # Prepare event
            event.owner = self
            event.type = name
            # Fire it
            for handler in handlers:
                if isinstance(handler, list):
                    ob, name = handler
                    ob[name](event)
                else:
                    handler(event)
        
        def _proxy_event(self, element, name):
            """ Easily get JS events from DOM elements in our event system.
            """
            that = this
            element.addEventListener(name, lambda ev: that.emit_event(name, {'cause': ev}), False)
        
        def _connect_js_event(self, element, event_name, method_name):
            """ Connect methods of this object to JS events.
            """
            that = this
            element.addEventListener(event_name, lambda ev: that[method_name](ev), False)
    
    ## Static methods
    
    @classmethod
    def get_js(cls):
        # todo: move this to app/clientcode
        cls_name = 'flexx.classes.' + cls.__name__
        base = object if (cls is Paired) else cls.mro()[1]
        base_class = 'Object'
        if cls is not Paired:
            base_class = 'flexx.classes.%s.prototype' % cls.mro()[1].__name__
        
        # # Collect event names
        # event_names = set()
        # for c in cls.mro():
        #     event_names.update(c._EVENT_NAMES)
        #     if c is Paired:
        #         break
        
        js = []
        js.extend(get_class_definition(cls_name, base_class))
        
        # js.append('%s.prototype._EVENT_NAMES = %r;\n' % (cls_name, list(event_names)))
        
        # # Main functions
        # # todo: flexx.classes.xx
        # # todo: we could reduce JS code by doing inheritance in JS
        # js.append('flexx.classes.%s = ' % cls_name)
        # js.append(cls.__jsinit__.jscode
        
        # JS = cls.__dict__.get('JS', None)
        # if JS is not None:
        #     
        #     for key, val in JS.__dict__.items():
        #         
        #         if isinstance(val, Signal):
                    
        
        
        
        
        for key, func in cls.__dict__.items():
            # Methods
            # func = getattr(cls, key)
            if isinstance(func, JSCode):
                code = func.jscode.replace('super()', base_class)  # fix super
                name = func.name
                js.append('%s.prototype.%s = %s' % (cls_name, name, code))
            
            # Property json methods
            # todo: implement property functions for validation, to_json and from_json in flexx.props
            # todo: more similar API and prop handling in py and js
            elif isinstance(func, Prop) and hasattr(func, 'validate'):
                prop = func
                propname = key
                funcs = [getattr(prop, x, None) for x in ('to_json__js', 'from_json__js')]
                funcs = [func for func in funcs if func is not None]
                for func in funcs:
                    code = func.jscode
                    name = '_%s_%s' % (func.name, propname)
                    js.append('%s.prototype.%s = %s' % (cls_name, name, code))
        
        # todo: give it an id
        return '\n'.join(js)
    
    @classmethod
    def get_css(cls):
        return cls.__dict__.get('CSS', '')
