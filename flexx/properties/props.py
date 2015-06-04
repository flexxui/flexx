""" Implementation of property classes.
"""

import sys
import json

from .base import Prop

if sys.version_info[0] >= 3:
    string_types = str,
else:
    string_types = basestring,


class Bool(Prop):
    """ Stores a boolean value. Converts a set value to bool.
    The default value is False.
    """
    _default = False
    
    def validate(self, val):
        return bool(val)


class Int(Prop):
    """ Stores an integer value. Converts a set value to int.
    The default value is 0.
    """
    _default = 0
    # todo: min, max?
    def validate(self, val):
        return int(val)  # accept int, float, numpy scalar, and even str


class Float(Prop):
    """ Stores a float value. Converts a set value to int.
    The default value is 0.0.
    """
    _default = 0.0
    
    def validate(self, val):
        return float(val)  # accept int, float, numpy scalar, and even str


class Str(Prop):
    """ Stores a string. Requires set value to be a string.
    The default value is the empty string.
    """
    _default = ''
    
    def validate(self, val):
        if not isinstance(val, string_types):
            raise ValueError('Str prop %r requires a string.' % self.name)
        return val


class Tuple(Prop):
    """ Stores a tuple of object of another property type. Accepts a
    tuple or set as input, each element is validated by the property
    class corresponding to the item_type.
    """
    _default = ()
    # todo: allowed lengths?
    def __init__(self, item_type, default=None, help=None):
        self._item_prop = item_type()
        Prop.__init__(self, default, help)
        assert isinstance(item_type, type) and issubclass(item_type, Prop)
        #item_type = item_type if isinstance(item_type, tuple) else (item_type, )
        #self._item_types = item_type
    
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


class FloatPair(Tuple):
    """ Store a tuple of two floats, and allow setting using a single
    scalars (setting both to the same value). Convenient for values that
    apply to two dimensions, like size, position and flex values.
    """
    _default = 0.0, 0.0
    
    def __init__(self, default=None, help=None):
        Tuple.__init__(self, Float, default, help)
    
    def validate(self, val):
        if isinstance(val, (int, float)):
            return float(val), float(val)
        elif isinstance(val, (tuple, list)):
            if len(val) != 2:
                raise ValueError('FloatPair prop needs two values, not %i' % len(val))
            return tuple([self._item_prop.validate(e) for e in val])
        else:
            raise ValueError('FloatPair prop %r requires float, tuple or list.' % self.name)


class Color(Prop):
    """ Stores a color. RGB tuple, hex values. etc. Not really
    implemented yet. Only supports tuples and 3 string color names.
    """
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
    """ Stores an instance of a certain type. The instance must be
    a hashable object.
    """
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
