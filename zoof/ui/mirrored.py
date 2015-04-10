""" Base class for objects that live in both Python and JS
"""

import sys
import weakref
import json

if sys.version_info[0] >= 3:
    string_types = str,
else:
    string_types = basestring,


# From six.py
def with_metaclass(meta, *bases):
    """Create a base class with a metaclass."""
    # This requires a bit of explanation: the basic idea is to make a dummy
    # metaclass for one level of class instantiation that replaces itself with
    # the actual metaclass.
    class metaclass(meta):
        def __new__(cls, name, this_bases, d):
            return meta(name, bases, d)
    return type.__new__(metaclass, 'temporary_class', (), {})


class Prop(object):
    """ A prop can be assigned to a class attribute.
    
    To use props, simply assign them as class attributes::
    
        class Foo(HasProps):
            size = Int(3, 'The size of the foo')
            title = Str('nameless', 'The title of the foo')
    
    To create new props, inherit from Prop and implement validate()::
    
        class MyProp(Prop):
            _default = None  # The default for when no default is given
            def validate(self, val):
                assert isinstance(val, int, float)  # require scalars
                return float(val)  # always store as float
    
    Any prop can only store hashable objects. This includes tuples,
    provided that the items it contains are hashable too. A prop may
    accept* nonhashable values (e.g. list), but the data must be stored
    as an immutable object.
    
    Prop objects are attached to classes, and behave like properties
    because they implement the data descriptor protocol (__get__,
    __set__, and __delete__). The actual value is stored on the instance
    of the class that the prop applies to.
    
    """
    _default = None  # The class _default is the default when no default is given
    
    def __init__(self, default=None, help=None):
        # Init name, set the first time that an instance is created
        self._name = None
        # Set default to prop-default if not given and validate
        default = self._default if default is None else default
        self._default = self.validate(default)
        # Set doc
        self.__doc__ = help or 'A %s property' % self.__class__.__name__
    
    def __get__(self, obj, objType=None):
        if obj is not None:
            return self._get(obj)
        elif objType is not None:
            return self
        else:
            raise ValueError("both 'obj' and 'owner' are None, don't know what to do")
    
    def _get(self, obj):
        """ Get the value from the object that this is a prop of. 
        """
        # if not hasattr(obj, self._private_name):
        #     setattr(obj, self._private_name, self.default)
        return getattr(obj, self._private_name)
    
    def __set__(self, obj, value):
        # todo: check readonly
        self._set(obj, value)
    
    def _set(self, obj, value):
        """ Set the value from the object that this a prop of. This
        bypasses read-only, thus forming a way for classes to set
        read-only attributes internally.
        """
        # Validate value, may return a "cleaned up" version
        value = self.validate(value)
        
        # Get hash. We force all prop values to be hashable. There is
        # no point in having prop change notification if the values are
        # mutable.
        try:
            newhash = hash(value)
        except TypeError:
            raise TypeError('Prop values need to be hashable, %r is not.' % 
                            type(value).__name__)
        
        # If same as old value, early exit
        old = self._get(obj)
        #if value == old:
        oldhash = getattr(obj, self._private_name + '_hash')
        if newhash == oldhash:
            return
        else:
            setattr(obj, self._private_name + '_hash', newhash)
        
        # Apply
        setattr(obj, self._private_name, value)
        
        # Notify, first dynamic, then static, just like IPython traits
        callbacks = []
        callbacks += obj._prop_listeners.get(self.name, ())
        callbacks += obj._prop_listeners.get('', ())  # any prop
        callback = getattr(obj, '_%s_changed' % self.name, None)
        if callback is not None:
            callbacks.append(callback)
        
        for callback in callbacks:
            # todo:  allow less args: https://github.com/ipython/ipython/blob/master/traitlets/traitlets.py#L661
            callback(self.name, old, value)
    
    def __delete__(self, obj):
        if hasattr(obj, self._private_name):
            delattr(obj, self._private_name)
    
    @property
    def name(self):
        return self._name
    
    @property
    def _private_name(self):
        return '_' + self._name
    
    @property
    def default(self):
        return self._default
    
    def validate(self, value):
        raise NotImplementedError()
    
    def to_json(self, value):
        return json.dumps(value)
    
    def from_json(self, txt):
        return json.loads(txt)


# Note, we need Prop defined before HasProps, because we need to test
# isinstance(cls, Prop) in the meta class (on class creation)


class HasPropsMeta(type):
    """ Meta class for HasProps
    * Sets __props__ attribute on the class
    * Set the name of each prop
    * Initialize value for each prop (to default)
    """
    
    CLASSES = []
    
    def __init__(cls, name, bases, dct):
        
        HasPropsMeta.CLASSES.append(cls)  # todo: dict by full qualified name?
        
        # Collect props defined on the given class
        props = {}
        for name, prop in dct.items():
            if isinstance(prop, type) and issubclass(prop, Prop):
                prop = prop()
                setattr(cls, name, prop)  # allow setting just class
            if isinstance(prop, Prop):
                props[name] = prop
        # Finalize all found props
        for name, prop in props.items():
            assert prop._name is None
            prop._name = name
            setattr(cls, prop._private_name, prop.default)
            setattr(cls, prop._private_name + '_hash', hash(prop.default))
        # Cache prop names
        cls.__props__ = set(props.keys())
        # Proceeed as normal
        type.__init__(cls, name, bases, dct)


class HasProps(with_metaclass(HasPropsMeta, object)):
    """ A base class for objects that have props.
    
    """
    
    def __init__(self, **kwargs):
        # Callbacks for each property
        self._prop_listeners = {}
        # Assign 
        for name, val in kwargs.items():
            setattr(self, name, val)
    
    def add_listener(self, prop_name, callback):
        """ Add a callback for the given property.
        
        When the value of that property changes, the callback is
        called with three parametes: name, old value, new value.
        """
        callbacks = self._prop_listeners.setdefault(prop_name, [])
        callbacks.append(callback)
        # todo: smarter system using weakref to object and method name to avoid mem leak
    
    # todo: or simply allow _set_prop(name, old, new)? who needs to be aware
    # of changes? If only subclasses, don't bother with a callback system ...
    
    @classmethod
    def props(cls, withbases=True):
        props = set()
        def collect(cls):
            props.update(cls.__props__)
            if withbases:
                for base in cls.__bases__:
                    if hasattr(base, '__props__'):
                        collect(base)
        collect(cls)
        return props
    
    def _set_prop(self, name, value):
        """ Method to set a property. 
        """
        getattr(self.__class__, name)._set(self, value)
    
    
    def __setattr__(self, name, value):
        if name.startswith("_"):
            super(HasProps, self).__setattr__(name, value)
        else:
            props = self.props()
            if name in props:
                super(HasProps, self).__setattr__(name, value)
            else:
                matches, text = props, "possible"
                raise AttributeError("unexpected attribute %r to %s." %
                                    (name, self.__class__.__name__))


## The propery implementations

class Bool(Prop):
    _default = False
    
    def validate(self, val):
        return bool(val)


class Int(Prop):
    _default = 0
    # todo: min, max?
    def validate(self, val):
        if not isinstance(val, (int, float)):
            raise ValueError('Int prop %r requires a scalar.' % self.name)
        return int(val)


class Float(Prop):
    _default = 0.0
    
    def validate(self, val):
        if not isinstance(val, (int, float)):
            raise ValueError('Float prop %r requires a scalar.' % self.name)
        return float(val)


class Str(Prop):
    _default = ''
    
    def validate(self, val):
        if not isinstance(val, str):
            raise ValueError('Str prop %r requires a string.' % self.name)
        return val


class Tuple(Prop):
    _default = ()
    # todo: allowed lengths?
    def __init__(self, item_type, default=None, help=None):
        Prop.__init__(self, default, help)
        assert isinstance(item_type, type) and issubclass(item_type, Prop)
        #item_type = item_type if isinstance(item_type, tuple) else (item_type, )
        #self._item_types = item_type
        self._item_prop = item_type()
    
    def validate(self, val):
        if isinstance(val, (tuple, list)):
            return tuple([self._item_prop.validate(e) for e in val])
        else:
            raise ValueError('Tuple prop %r requires tuple or list.' % self.name)
    
    def to_json(self, val):
        jsonparts = [self._item_prop.to_json(e) for e in val]
        pyparts = [json.loads(txt) for txt in jsonparts]
        return json.dumps(pyparts)
    
    def from_json(self, txt):
        pyparts = json.loads(txt)
        jsonparts = [json.dumps(e) for e in pyparts]
        return [self._item_prop.from_json(txt) for txt in jsonparts]


class Color(Prop):
    _default = (1, 1, 1)
    
    # todo: this is a stub. Need HTML names, #rgb syntax etc.
    _color_names = {'red': (1, 0, 0), 'green': (0, 1, 0), 'blue': (0, 0, 1)}
    
    def validate(self, val):
        if isinstance(val, string_types):
            val = val.lower()
            if val in self._color_names:
                return self._color_names[val]
            else:
                raise ValueError('Color prop %r does not understand '
                                 'given string.' % self.name)
        elif isinstance(val, tuple):
            val = tuple([float(v) for v in val])
            if len(val) in (3, 4):
                return val
            else:
                raise ValueError('Color prop %r needs tuples '
                                 'of 3 or 4 elements.' % self.name)
        else:
            raise ValueError('Color prop %r requires str or tuple.' % self.name)

    

class Instance(Prop):
    _default = None
    
    def __init__(self, item_type, default=None, help=None):
        Prop.__init__(self, default, help)
        item_type = item_type if isinstance(item_type, tuple) else (item_type, )
        self._item_types = item_type
    
    def validate(self, val):
        if val is None:
            return val
        elif isinstance(val, self._item_types):
            return val
        else:
            item_types = ', '.join([t.__name__ for t in self._item_types])
            this_type = val.__class__.__name__
            raise ValueError('Instance prop %r needs items to be in '
                             '[%s], but got %s.' % 
                             (self.name, item_types, this_type))
    
    
## -----
# todo: the above is generic and need to go in utils, below is JS related


def get_mirrored_classes():
    return [c for c in HasPropsMeta.CLASSES if issubclass(c, Mirrored)]

def get_instance_by_id(id):
    """ Get js object corresponding to the given id, or None if it does
    not exist. 
    """
    return Mirrored._instances.get(id, None)

from zoof.ui.compile import js

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
        from zoof.ui.app import get_default_app
        self._app = get_default_app()
        Mirrored._counter += 1
        self.id = self.__class__.__name__ + str(Mirrored._counter)
        
        Mirrored._instances[self._id] = self
        
        
        import json
        clsname = self.__class__.__name__
        props = {}
        for name in self.props():
            val = getattr(self, name)
            props[name] = getattr(self.__class__, name).to_json(val)
        cmd = 'zoof.widgets.%s = new zoof.%s(%s);' % (self.id, clsname, json.dumps(props))
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
        cmd = 'zoof.widgets.%s._set_prop_from_py(%r, %r);' % (self.id, name, txt)
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
            zoof.ws.send('PROP ' + self.id + ' ' + name + ' ' + txt)
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
    def get_js(cls):
        cls_name = cls.__name__
        js = []
        
        # Main functions
        # todo: zoof.classes.xx
        # todo: we could reduce JS code by doing inheritance in JS
        js.append('zoof.%s = ' % cls_name)
        js.append(cls.__jsinit__.js.jscode)
        
        for key in dir(cls):
            # Methods
            func = getattr(cls, key)
            if hasattr(func, 'js') and hasattr(func.js, 'jscode'):
                code = func.js.jscode
                name = func.js.name
                js.append('zoof.%s.prototype.%s = %s' % (cls_name, name, code))
            
            # Property json methods
            # todo: implement property functions for validation, to_json and from_json in zoof.props
            # todo: more similar API and prop handling in py and js
            elif isinstance(func, Prop) and hasattr(func, 'validate'):
                prop = func
                propname = key
                funcs = [getattr(prop, x, None) for x in ('to_json__js', 'from_json__js')]
                funcs = [func for func in funcs if func is not None]
                for func in funcs:
                    code = func.js.jscode
                    name = '_%s_%s' % (func.js.name, propname)
                    js.append('zoof.%s.prototype.%s = %s' % (cls_name, name, code))
        
        return '\n'.join(js)
    
    @classmethod
    def get_css(cls):
        return cls.CSS


class Foo(HasProps):
    
    size = Int(help='the size of the foo')
    
    def __init__(self, x, **kwargs):
        HasProps.__init__(self, **kwargs)
        self._x = x
    
    def methodb(self):
        """ this is method b"""
        pass


class Bar(Foo):
    color = Color
    names = Tuple(Str)
    

if __name__ == '__main__':
    a = Bar(1, size=4)
#Foo.size.__doc__ = 'asd'
    