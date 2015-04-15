""" Implementation of base Prop object and the HasProps base class.
"""

import sys
import weakref
import json


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
    """ Base class for all properties.
    
    The ``default`` argument sets the default value that instances of
    the current class will have for this property. If not given, the
    default value of the property class is used.
    
    If ``help`` is given, it is set as the docstring of the propery,
    where tools like IDE's and documentation builders can access it.
    
    Prop objects are attached to classes, and behave like properties
    because they implement the data descriptor protocol. The actual
    value is stored on the instance of the class that the property
    applies to.
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
    """ The base class for objects that have properties. Any class that
    want to use properties must inherit from this class.
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
