""" Base class for objects that live in both Python and JS

This basically implements the syncing of properties.
"""

import sys
import json
import weakref
import hashlib

from ...properties import HasPropsMeta, HasProps, Prop, Int, Str
from ...pyscript import js, JSCode
from ...pyscript.parser2 import get_class_definition

if sys.version_info[0] >= 3:
    string_types = str,
else:
    string_types = basestring,


def get_mirrored_classes():
    """ Get a list of all known mirrored classes.
    """
    return [c for c in HasPropsMeta.CLASSES if issubclass(c, Mirrored)]


def get_instance_by_id(id):
    """ Get instance of Mirrored class corresponding to the given id,
    or None if it does not exist.
    """
    return Mirrored._instances.get(id, None)


class Mirrored(HasProps):
    """ 
    Subclass of HasProps for which the instances have a mirror object
    in JS. The propertiess of the two are synchronised.
    """
    
    # Keep track of all instances, so we can easily collect al JS/CSS
    _instances = weakref.WeakValueDictionary()
    
    # Count instances to give each instance a unique id
    _counter = 0
    
    # CSS for this class (no css in the base class)
    CSS = ""
    
    # Names of events
    _EVENT_NAMES = []
    
    # Properties:
    
    id = Str(help='The unique id of this Mirrored instance')  # todo: readonly
    
    def __init__(self, **kwargs):
        HasProps.__init__(self, **kwargs)
        
        # Associate with an app
        from flexx.ui.app import get_default_app, get_current_app  # avoid circular import
        self._app = get_current_app()
        self._app.register_mirrored(self.__class__)  # Ensure the app knows us
        
        # Set id and register this instance
        Mirrored._counter += 1
        self.id = self.__class__.__name__ + str(Mirrored._counter)
        Mirrored._instances[self._id] = self
        
        # Instantiate JavaScript version of this class
        clsname = 'flexx.classes.' + self.__class__.__name__
        props = {}
        for name in self.props():
            val = getattr(self, name)
            props[name] = getattr(self.__class__, name).to_json(val)
        cmd = 'flexx.instances.%s = new %s(%s);' % (self.id, clsname, json.dumps(props))
        self._app._exec(cmd)
        
        # todo: get notified when a prop changes, pend a call via call_later
        # todo: collect more changed props if they come by
        # todo: in the callback send all prop updates to js
        
        # Register callbacks
        for name in self.props():
            self.add_listener(name, self._sync_prop)
    
    # def call_method(self, code):
    #     cmd = 'flexx.instances.%s.%s' % (self.id, code)
    #     self._app._exec(cmd)
    
    @js
    def _js__init__(self, props):
        
        # Set id alias. In most browsers this shows up as the first element
        # of the object, which makes it easy to identify objects while
        # debugging. This attribute should *not* be used.
        self.__id = props['id']
        
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
    
    @js
    def _js_init(self):
        pass  # Subclasses should overload this
    
    ## Dealing with props
    
    def _sync_prop(self, name, old, new):
        """ Callback to sync properties to JS
        """
        # Note: the JS function _set_property is defined below
        txt = getattr(self.__class__, name).to_json(new)
        #print('sending json', txt)
        cmd = 'flexx.instances.%s._set_property(%r, %r, true, true);' % (self.id, name, txt)
        self._app._exec(cmd)
    
    @js
    def _js_set_property(self, name, val, fromjson=False, emit=True):
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
    
    @js
    def _js_getter_setter(name):
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
            flexx.ws.send('PROP ' + self.id + ' ' + name + ' ' + txt)
        return getter, setter
    
    ## JS event system
    
    @js
    def _js_has_handler(self, handler, handlers):
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
    
    @js
    def connect_event_js(self, name, handler):
        if name not in self._event_handlers:
            raise ValueError('Event %s not known' % name)
        handlers = self._event_handlers[name]
        if not self._has_handler(handler, handlers):
            handlers.append(handler)
    
    @js
    def disconnect_event_js(self, name, handler):
        if name not in self._event_handlers:
            raise ValueError('Event %s not known' % name)
        handlers = self._event_handlers[name]
        while self._has_handler(handler, handlers):
            handlers.remove(handler)
    
    @js
    def emit_event_js(self, name, event):
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
    
    @js
    def _js_proxy_event(self, element, name):
        """ Easily get JS events from DOM elements in our event system.
        """
        that = this
        element.addEventListener(name, lambda ev: that.emit_event(name, {'cause': ev}), False)
    
    ## Static methods
    
    @classmethod
    def get_js(cls):
        # todo: move this to app/clientcode
        cls_name = 'flexx.classes.' + cls.__name__
        base = object if (cls is Mirrored) else cls.mro()[1]
        base_class = 'Object'
        if cls is not Mirrored:
            base_class = 'flexx.classes.%s.prototype' % cls.mro()[1].__name__
        
        # Collect event names
        event_names = set()
        for c in cls.mro():
            event_names.update(c._EVENT_NAMES)
            if c is Mirrored:
                break
        
        js = []
        js.extend(get_class_definition(cls_name, base_class))
        
        js.append('%s.prototype._EVENT_NAMES = %r;\n' % (cls_name, list(event_names)))
        
        # # Main functions
        # # todo: flexx.classes.xx
        # # todo: we could reduce JS code by doing inheritance in JS
        # js.append('flexx.classes.%s = ' % cls_name)
        # js.append(cls.__jsinit__.jscode
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
