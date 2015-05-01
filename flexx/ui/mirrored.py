""" Base class for objects that live in both Python and JS
"""

import sys
import weakref
import json
import hashlib

from ..properties import HasPropsMeta, HasProps, Prop, Int, Str
from ..pyscript import js, JSCode

if sys.version_info[0] >= 3:
    string_types = str,
else:
    string_types = basestring,


def get_mirrored_classes():
    return [c for c in HasPropsMeta.CLASSES if issubclass(c, Mirrored)]


def get_instance_by_id(id):
    """ Get js object corresponding to the given id, or None if it does
    not exist. 
    """
    return Mirrored._instances.get(id, None)


class Mirrored(HasProps):
    """ Instances of this class will have a mirror object in JS. The
    props of the two are synchronised.
    """
    
    _instances = weakref.WeakValueDictionary()
    
    CSS = ""
    
    name = Str()
    id = Str()  # todo: readonly
    
    _counter = 0
    
    def __init__(self, **kwargs):
        HasProps.__init__(self, **kwargs)
        from flexx.ui.app import get_default_app, get_current_app  # avoid circular ref
        self._app = get_current_app()
        Mirrored._counter += 1
        self.id = self.__class__.__name__ + str(Mirrored._counter)
        
        Mirrored._instances[self._id] = self
        
        # Make sure we can use this class in JS
        self._app.register_mirrored(self.__class__)
        
        import json
        clsname = self.__class__.__name__
        props = {}
        for name in self.props():
            val = getattr(self, name)
            props[name] = getattr(self.__class__, name).to_json(val)
        cmd = 'flexx.instances.%s = new flexx.classes.%s(%s);' % (self.id, clsname, json.dumps(props))
        print(cmd)
        self._app._exec(cmd)
        
        # todo: get notified when a prop changes, pend a call via call_later
        # todo: collect more changed props if they come by
        # todo: in the callback send all prop updates to js
        
        # Register callbacks
        for name in self.props():
            if name in ('children', ):
                continue  # todo: implement via Tuple(WidgetProp, sync=False)?
            self.add_listener(name, self._sync_prop)
    
    def get_app(self):
        return self._app
    
    # @property
    # def id(self):
    #     return self._id
    
    def _sync_prop(self, name, old, new):
        print('_sync_prop', name, new)
        txt = getattr(self.__class__, name).to_json(new)
        print('sending json', txt)
        cmd = 'flexx.instances.%s._set_prop_from_py(%r, %r);' % (self.id, name, txt)
        self._app._exec(cmd)
    
    def call_method(self, code):
        cmd = 'flexx.instances.%s.%s' % (self.id, code)
        self._app._exec(cmd)
    
    def methoda(self):
        """ this is method a """
        pass
    
    @js
    def test_js_method(self):
        alert('Testing!')
    
    @js
    def _set_prop_from_py(self, name, val, tojson=True):
        # To set props from Python without sending a sync pulse back
        # and also to convert from json
        if tojson:
            if self['_from_json_'+name]:  # == function 
                val = self['_from_json_'+name](val)
            else:
                val = JSON.parse(val)
            val = None if val is undefined else val
        #print('_set_prop_from_py', name, val)
        # if self['_set_'+name]:
        #     val2 = self['_set_' + name](val)
        #     if val2 is not undefined:
        #         val = val2
        old = self['_' + name]
        self['_' + name] = val
        if self['_'+name+'_changed']:
            self['_'+name+'_changed'](name, old, val)
    
    @js
    def _getter_setter(name):
        # Provide scope for closures
        def getter():
            if self['_get_'+name]:
                return self['_get_' + name]()
            else:
                return self['_' + name]
        def setter(val):
            self._set_prop_from_py(name, val, False)
            value = self['_' + name]
            if self['_to_json_'+name]:  # == function
                txt = self['_to_json_'+name](value)
            else:
                txt = JSON.stringify(value)
            flexx.ws.send('PROP ' + self.id + ' ' + name + ' ' + txt)
        return getter, setter
    
    @js
    def __jsinit__(self, props):
        
        # Set id alias. In most browsers this shows up as the first element
        # of the object, which makes it easy to identify objects while
        # debugging. This attribute should *not* be used.
        self.__id = props['id']
        
        # Create properties
        for name in props:
            opts = {"enumerable": True}
            gs = self._getter_setter(name)
            opts['get'] = gs[0]
            opts['set'] = gs[1]
            Object.defineProperty(self, name, opts)
        
        # Init
        if self._jsinit:
            self._jsinit()
        # Assign initial values
        for name in props:
            self['_'+name] = None  # init
            self._set_prop_from_py(name, props[name])
    
    @classmethod
    def get_jshash(cls):
        # todo: when we cache code to the filesystem, this hash needs to be based on code
        return hashlib.sha256(cls.__name__.encode()).digest()
    
    @classmethod
    def get_js(cls):
        cls_name = cls.__name__
        js = []
        
        # Main functions
        # todo: flexx.classes.xx
        # todo: we could reduce JS code by doing inheritance in JS
        js.append('flexx.classes.%s = ' % cls_name)
        js.append(cls.__jsinit__.jscode)
        
        for key in dir(cls):
            # Methods
            func = getattr(cls, key)
            if isinstance(func, JSCode):
                code = func.jscode
                name = func.name
                js.append('flexx.classes.%s.prototype.%s = %s' % (cls_name, name, code))
            
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
                    js.append('flexx.classes.%s.prototype.%s = %s' % (cls_name, name, code))
        
        # todo: give it an id
        return '\n'.join(js)
    
    @classmethod
    def get_css(cls):
        return cls.CSS
