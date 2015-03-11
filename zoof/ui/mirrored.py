""" Base class for objects that live in both Python and JS
"""

import sys

if sys.version_info[0] >= 3:
    string_types = str,
else:
    string_types = basestring,


def is_immutable(ob):
    """ Test whether an object is immutable.
    """
    if ob is None:
        return True
    elif isinstance(ob, (bool, int, float, string_types)):
        return True
    elif isinstance(ob, tuple):
        for child in ob:
            if not is_immutable(child):
                return False
        return True
    else:
        return False


def has_props(cls):
    """ Finalize the props found on the given class and its bases.
    
    You create a class, no matter where it inherits from, decorate it
    with this function, and your props will work. However, by instead
    inheriting from HasProps you get a few extra nicities.
    """
    # Check if we can exit early 
    if '__props__' in cls.__dict__:
        return cls
    # Collect props defined on the given class
    props = {}
    for name, prop in cls.__dict__.items():
        if isinstance(prop, type) and issubclass(val, Prop):
            props[name] = prop()
        if isinstance(prop, Prop):
            props[name] = prop
    # Finalize all found props
    for name, prop in props.items():
        if not prop._name:
            prop._name = name
            setattr(cls, prop._private_name, prop.default)
    # Assign props for this class (this marks the props as finalized)
    cls.__props__ = set(props.keys())
    # Recurse to base classes
    for base in cls.__bases__:
        if base not in (object, HasProps):
            has_props(base)
    return cls


class HasProps(object):
    """ A base class for objects that have props.
    
    """

    # Some implementations of this pattern (e.g. Bokeh) use metaclasses
    # to finalize the props. However, the props really only need to be
    # finalized when being used on instances. Therefore I went with
    # this lighter approach (at least for now).
    
    def __init__(self, **kwargs):
        # Variables changed since creation
        self._changed_props = set()
        # Finalize props (e.g. ensure they have a name)
        has_props(self.__class__)
        # Assign 
        for name, val in kwargs.items():
            setattr(self, name, val)
        self.reset_changed_props()
    
    @property
    def changed_props(self):
        """ Get a set of names of props that changed since object creation
        or the last call to reset_changed_props().
        """
        return _changed_props
    
    def reset_changed_props(self):
        self._changed_props = set()
    
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
    
    def __setattr__(self, name, value):
        if name.startswith("_"):
            super(HasProps, self).__setattr__(name, value)
        else:
            props = sorted(self.props())
            if name in props:
                super(HasProps, self).__setattr__(name, value)
            else:
                matches, text = props, "possible"
                raise AttributeError("unexpected attribute %r to %s." %
                                    (name, self.__class__.__name__))


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
    
    Any prop can only store immutable objects. This includes tuples,
    provided that the items it contains are immutable too. A prop may
    accept* mutable values, but the data must be stored as an immutable
    object.
    
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
    
    def __set__(self, obj, value):
        # Validate value, may return a "cleaned up" version
        value = self.validate(value)
        assert is_immutable(value)
        
        # If same as old value, early exit
        old = self._get(obj)
        if value == old:
            return
        
        # Update
        if hasattr(obj, '_changed_props'):
            obj._changed_props.add(self.name)
        setattr(obj, self._private_name, value)
        
        # if hasattr(obj, '_trigger'):
        #     if hasattr(obj, '_block_callbacks') and obj._block_callbacks:
        #         obj._callback_queue.append((self.name, old, value))
        #     else:
        #         obj._trigger(self.name, old, value)

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
    
    def _get(self, obj):
        """ Get the value from the object that this is a prop of. """
        # if not hasattr(obj, self._private_name):
        #     setattr(obj, self._private_name, self.default)
        return getattr(obj, self._private_name)
    
    def validate(self, value):
        raise NotImplementedError()
    

class Bool(Prop):
    _default = False
    
    def validate(self, val):
        return bool(val)


class Int(Prop):
    _default = 0
    
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
    
    def __init__(self, item_type, default=None, help=None):
        Prop.__init__(self, default, help)
        item_type = item_type if isinstance(item_type, tuple) else (item_type, )
        self._item_types = item_type
    
    def validate(self, val):
        
        if isinstance(val, (tuple, list)):
            for e in val:
                if not isinstance(e, self._item_types):
                    item_types = ', '.join([t.__name__ for t in self._item_types])
                    this_type = e.__class__.__name__
                    raise ValueError('Tuple prop %r needs items to be in '
                                     '[%s], but got %s.' % 
                                     (self.name, item_types, this_type))
            return val
        else:
            raise ValueError('Tuple prop %r requires tuple or list.' % self.name)


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


# todo: the above is generic and need to go in utils, below is JS related


MIRRORED_CLASSES = []

# todo: arg, we need metaclass anyway
def is_mirrored(cls):
    MIRRORED_CLASSES.append(cls)
    return cls

@has_props
@is_mirrored
class Mirrored(HasProps):
    """ Instances of this class will have a mirror object in JS. The
    props of the two are synchronised.
    """
    
    name = Str()
    _counter = 0
    
    def __init__(self, **kwargs):
        HasProps.__init__(self, **kwargs)
        from .app import current_app
        self._app = current_app()
        Mirrored._counter += 1
        self._id = self.__class__.__name__ + str(Mirrored._counter)
        
        import json
        funcname = self.__class__.__name__
        props = {}
        for name in self.props():
            props[name] = getattr(self, name)
        self._app._exec('zoof.widgets.%s = new zoof.%s(%s);' % (self.id, funcname, json.dumps(props)))
        
    @property
    def id(self):
        return self._id
    
    def methoda(self):
        """ this is method a """
        pass
    
    @classmethod
    def get_js(cls):
        cls_name = cls.__name__
        js = []
        # Main functions
        js.append('zoof.%s = function (props) {' % cls_name)
        js.append('    for (var name in props) {')
        js.append('        if (props.hasOwnProperty(name)) {')
        js.append('            this["_" + name] = props[name];')
        js.append('        }')
        js.append('    }')
        js.append('};')
        # Property setters and getters
        # todo: do we need *all* properties to be mirrored in JS?
        # todo: we could reduce JS code by doing inheritance in JS
        for name in cls.props():  # todo: only works if there was once an instance
            js.append('zoof.%s.prototype.set_%s = function (val) {' % (cls_name, name))
            js.append('    this._%s = val;' % name)
            js.append('};')
            js.append('zoof.%s.prototype.get_%s = function () {' % (cls_name, name))
            js.append('    return this._%s;' % name)
            js.append('};')
        # Methods
        return '\n'.join(js)
        
            
            
        
        
        
        

class Foo(Mirrored):
    
    size = Int(help='the size of the foo')
    color = Color()
    names = Tuple(str)
    
    def __init__(self, x, **kwargs):
        Mirrored.__init__(self, **kwargs)
        self._x = x
    
    def methodb(self):
        """ this is method b"""
        pass
    
    
if __name__ == '__main__':
    a = Foo(1, size=4)
#Foo.size.__doc__ = 'asd'
    