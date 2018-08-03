"""
Implements the property class and subclasses.
"""

from ._loop import loop, this_is_js
from ._action import BaseDescriptor
from ._dict import Dict

undefined = None


class Property(BaseDescriptor):
    """ Base property class. Properties are (readonly) attributes associated
    with :class:`Component <flexx.event.Component>` classes, which can be
    :func:`mutated <flexx.event.Component._mutate>` only by
    :class:`actions <flexx.event.Action>`.
    The base ``Property`` class can have any value, the subclasses
    validate/convert the value when it is mutated.

    Arguments:
        initial_value: The initial value for the property. If omitted,
            a default value is used (specific for the type of property).
        settable (bool): If True, a corresponding setter action is
            automatically created that can be used to set the property.
            Default False.
        doc (str): The documentation string for this property (optional).

    Example usage:

    .. code-block:: python

        class MyComponent(event.Component):

            foo = event.AnyProp(7, doc="A property that can be anything")
            bar = event.StringProp(doc='A property that can only be string')
            spam = event.IntProp(8, settable=True)

        >> c = MyComponent()
        >> c.set_spam(9)  # use auto-generated setter action

    One can also implement custom properties:

    .. code-block:: python

        class MyCustomProp(event.Property):
            ''' A property that can only be 'a', 'b' or 'c'. '''

            _default = 'a'

            def _validate(self, value, name, data):
                if value not in 'abc':
                    raise TypeError('MyCustomProp %r must be "a", "b" or "c".' % name)
                return value

    """

    _default = None
    _data = None  # Configurable data

    def __init__(self, *args, doc='', settable=False):
        self._consume_args(*args)
        # Set doc
        if not isinstance(doc, str):
            raise TypeError('event.Property() doc must be a string.')
        self._doc = doc
        # Set settable
        self._settable = bool(settable)

        self._set_name('anonymous_property')

    def _consume_args(self, *args):
        # Set initial value
        if len(args) > 1:
            raise TypeError('event.Property() accepts at most 1 positional argument.')
        elif len(args) == 1:
            self._default = args[0]
            if callable(self._default):
                raise TypeError('event.Property() is not a decorator (anymore).')

    def _set_name(self, name):
        self._name = name  # or func.__name__
        self.__doc__ = self._format_doc(self.__class__.__name__, name, self._doc)

    def _set_data(self, data):
        # Callable in __init__
        self._data = data

    def __set__(self, instance, value):
        t = 'Cannot set property %r; properties can only be mutated by actions.'
        raise AttributeError(t % self._name)

    def __get__(self, instance, owner):
        if instance is None:
            return self
        private_name = '_' + self._name + '_value'
        loop.register_prop_access(instance, self._name)
        return getattr(instance, private_name)

    def make_mutator(self):
        flx_name = self._name
        def flx_mutator(self, *args):
            return self._mutate(flx_name, *args)
        return flx_mutator

    def make_set_action(self):
        flx_name = self._name
        def flx_setter(self, *val):
            self._mutate(flx_name, val[0] if len(val) == 1 else val)
        return flx_setter

    def _validate_py(self, value):
        # Called from Python
        return self._validate(value, self._name, self._data)

    def _validate(self, value, name, data):
        return value


## Basic properties

class AnyProp(Property):
    """ A property that can be anything (like Property). Default None.
    """


class BoolProp(Property):
    """ A property who's values are converted to bool. Default False.
    """

    _default = False

    def _validate(self, value, name, data):
        return bool(value)


class TriStateProp(Property):
    """ A property who's values can be False, True and None.
    """

    _default = None

    def _validate(self, value, name, data):
        if value is None:
            return None
        return bool(value)


class IntProp(Property):
    """ A propery who's values are integers. Floats and strings are converted.
    Default 0.
    """

    _default = 0

    def _validate(self, value, name, data):
        if (isinstance(value, (int, float)) or isinstance(value, bool) or
                                               isinstance(value, str)):
            return int(value)
        else:
            raise TypeError('Int property %r cannot accept %r.' % (name, value))


class FloatProp(Property):
    """ A propery who's values are floats. Integers and strings are converted.
    Default 0.0.
    """

    _default = 0.0

    def _validate(self, value, name, data):
        if isinstance(value, (int, float)) or isinstance(value, str):
            return float(value)
        else:
            raise TypeError('Float property %r cannot accept %r.' % (name, value))


class StringProp(Property):
    """ A propery who's values are strings. Default empty string.
    """

    _default = ''

    def _validate(self, value, name, data):
        if not isinstance(value, str):
            raise TypeError('String property %r cannot accept %r.' % (name, value))
        return value


class TupleProp(Property):
    """ A propery who's values are tuples. In JavaScript the values are Array
    objects that have some of their methods disabled. Default empty tuple.
    """

    _default = ()

    def _validate(self, value, name, data):
        if not isinstance(value, (tuple, list)):
            raise TypeError('Tuple property %r cannot accept %r.' % (name, value))
        value = tuple(value)
        if this_is_js():  # pragma: no cover
            # Cripple the object so in-place changes are harder. Note that we
            # cannot prevent setting or deletion of items.
            value.push = undefined
            value.splice = undefined
            value.push = undefined
            value.reverse = undefined
            value.sort = undefined
        return value


class ListProp(Property):
    """ A propery who's values are lists. Default empty list. The value is
    always copied upon setting, so one can safely provide an initial list.

    Warning: updating the list in-place (e.g. use ``append()``) will not
    trigger update events! In-place updates can be done via the
    :func:`_mutate <flexx.event.Component._mutate>` method.
    """

    _default = []

    def _validate(self, value, name, data):
        if not isinstance(value, (tuple, list)):
            raise TypeError('List property %r cannot accept %r.' % (name, value))
        return list(value)


class DictProp(Property):
    """ A property who's values are dicts. Default empty dict. The value is
    always copied upon setting, so one can safely provide an initial dict.

    Warning: updating the dict in-place (e.g. use ``update()``) will not
    trigger update events! In-place updates can be done via the
    :func:`_mutate <flexx.event.Component._mutate>` method.
    """

    _default = {}

    def _validate(self, value, name, data):
        if not isinstance(value, dict):
            raise TypeError('Dict property %r cannot accept %r.' % (name, value))
        return value.copy()


class ComponentProp(Property):
    """ A propery who's values are Component instances or None. Default None.
    """

    _default = None

    def _validate(self, value, name, data):
        if not (value is None or hasattr(value, '_IS_COMPONENT')):
            raise TypeError('Component property %r cannot accept %r.' % (name, value))
        return value

## Advanced properties


class FloatPairProp(Property):
    """ A property that represents a pair of float values, which can also be
    set using a scalar.
    """

    _default = (0.0, 0.0)

    def _validate(self, value, name, data):
        if not isinstance(value, (tuple, list)):
            value = value, value
        if len(value) != 2:
            raise TypeError('FloatPair property %r needs a scalar '
                            'or two values, not %i' % (name, len(value)))
        if not isinstance(value[0], (int, float)):
            raise TypeError('FloatPair %r 1st value cannot be %r.' % (name, value[0]))
        if not isinstance(value[1], (int, float)):
            raise TypeError('FloatPair %r 2nd value cannot be %r.' % (name, value[1]))
        value = float(value[0]), float(value[1])
        if this_is_js():  # pragma: no cover
            # Cripple the object so in-place changes are harder. Note that we
            # cannot prevent setting or deletion of items.
            value.push = undefined
            value.splice = undefined
            value.push = undefined
            value.reverse = undefined
            value.sort = undefined
        return value


class EnumProp(Property):
    """ A property that represents a choice between a fixed set of (string) values.

    Useage: ``foo = EnumProp(['optionA', 'optionB', ...], 'default', ...)``.
    If no initial value is provided, the first option is used.
    """

    _default = ''

    def _consume_args(self, options, *args):
        if not isinstance(options, (list, tuple)):
            raise TypeError('EnumProp needs list of options')
        if not all([isinstance(i, str) for i in options]):
            raise TypeError('EnumProp options must be str')
        if not args:
            args = (options[0], )

        self._set_data([option.upper() for option in options])
        super()._consume_args(*args)

    def _validate(self, value, name, data):
        if not isinstance(value, str):
            raise TypeError('EnumProp %r value must be str.' % name)
        value = value.upper()
        if value.upper() not in data:
            raise ValueError('Invalid value for enum %r: %s' % (name, value))
        return value


class ColorProp(Property):
    """ A property that represents a color. The value is represented as a
    (dict-like) object that has the following attributes:

    * t: a 4-element tuple (RGBA) with values between 0 and 1.
    * css: a CSS string in the form 'rgba(r,g,b,a)'.
    * hex: a hex RGB color in the form '#rrggbb' (no transparency).
    * alpha: a scalar between 0 and 1 indicating the transparency.

    The color can be set using:

    * An object as described above.
    * A tuple (length 3 or 4) with floats between 0 and 1.
    * A hex RGB color like '#f00' or '#aa7711'.
    * A hex RGBA color like '#f002' or '#ff000022'.
    * A CSS string "rgb(...)" or "rgba(...)"
    * Simple Matlab-like names like 'k', 'w', 'r', 'g', 'b', etc.
    * A few common color names like 'red', 'yellow', 'cyan'.
    * Further, string colors can be prefixed with "light", "lighter",
      "dark" and "darker".
    * Setting to None or "" results in fully transparent black.
    """

    _default = '#000'  # Black

    def _validate(self, value, name, data):

        # We first convert to a tuple, and then derive the other values ...
        val = value

        common_colors = {  # A set of Matlab/Matplotlib colors and small CSS subset
            "k": '#000000', "black": "#000000",
            "w": '#ffffff', "white": '#ffffff',
            "r": '#ff0000', "red": '#ff0000',
            "g": '#00ff00', "green": '#00ff00', "lime": "#00ff00",
            "b": '#0000ff', "blue": '#0000ff',
            "y": '#ffff00', "yellow": '#ffff00',
            "m": '#ff00ff', "magenta": '#ff00ff', "fuchsia": "#ff00ff",
            "c": '#00ffff', "cyan": "#00ffff", "aqua": "#00ffff",
            "gray": "#808080", "grey": "#808080",
            }
        common_colors[''] = '#0000'  # empty string resolves to alpha 0, like None
        M = {'0': 0, '1': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7,
             '8': 8, '9': 9, 'a': 10, 'b': 11, 'c': 12, 'd': 13, 'e': 14, 'f': 15}
        Mi = '0123456789abcdef'

        # Convert from str
        if isinstance(val, str):
            val = val.lower()
            # Darker / lighter
            whitefactor = 0.0
            blackfactor = 0.0
            if val.startswith('darker'):
                blackfactor, val = 0.66, val[6:]
            elif val.startswith('dark'):
                blackfactor, val = 0.33, val[4:]
            elif val.startswith('lighter'):
                whitefactor, val = 0.66, val[7:]
            elif val.startswith('light'):
                whitefactor, val = 0.33, val[5:]
            # Map common colors
            val = common_colors.get(val, val)
            # Resolve CSS
            if val.startswith('#') and len(val) == 4 or len(val) == 5:
                val = [M.get(val[i], 0) * 17
                         for i in range(1, len(val), 1)]
            elif val.startswith('#') and len(val) == 7 or len(val) == 9:
                val = [M.get(val[i], 0) * 16 + M.get(val[i+1], 0)
                         for i in range(1, len(val), 2)]
            elif val.startswith('rgb(') or val.startswith('rgba('):
                val = [float(x.strip(' ,();')) for x in val[4:-1].split(',')]
                if len(val) == 4:
                    val[-1] = val[-1] * 255
            else:
                raise ValueError('ColorProp %r got invalid color: %r' % (name, value))
            # All values above are in 0-255
            val = [v / 255 for v in val]
            # Pull towards black/white (i.e. darken or lighten)
            for i in range(3):
                val[i] = (1.0 - whitefactor) * val[i] + whitefactor
                val[i] = (1.0 - blackfactor) * val[i] + 0

        # More converts / checks
        if val is None:
            val = [0, 0, 0, 0]  # zero alpha
        elif isinstance(val, dict) and 't' in val:
            val = val['t']

        # By now, the value should be a tuple/list
        if not isinstance(val, (tuple, list)):
            raise TypeError('ColorProp %r value must be str or tuple.' % name)

        # Resolve to RGBA if RGB is given
        val = [max(min(float(v), 1.0), 0.0) for v in val]
        if len(val) == 3:
            val = val + [1.0]
        elif len(val) != 4:
            raise ValueError('ColorProp %r value must have 3 or 4 elements, not %i' %
                             (name, len(val)))

        # Wrap up the tuple value
        val = tuple(val)
        if this_is_js():  # pragma: no cover
            # Cripple the object so in-place changes are harder. Note that we
            # cannot prevent setting or deletion of items.
            val.push = undefined
            val.splice = undefined
            val.push = undefined
            val.reverse = undefined
            val.sort = undefined

        # Now compose final object
        if this_is_js():
            d = {}
        else:
            d = Dict()
        d.t = val
        d.alpha = val[3]
        hex = [int(c * 255) for c in val[:3]]
        d.hex = '#' + ''.join([Mi[int(c / 16)] + Mi[c % 16] for c in hex])
        d.css = 'rgba({:.0f},{:.0f},{:.0f},{:g})'.format(
            val[0]*255, val[1]*255, val[2]*255, val[3])
        return d


# todo: For more complex stuff, maybe introduce an EitherProp, e.g. String or None.
# EiterProp would be nice, like Bokeh has. Though perhaps its already fine if
# props can be nullable. Note that people can also use AnyProp as a fallback.
#
# class NullProp(Property):
#
#     def _validate(self, value, name, data):
#         if not value is None:
#             raise TypeError('Null property can only be None.')
#
# class EitherProp(Property):
#
#     def __init__(self, *prop_classes, **kwargs):
#         self._sub_classes = prop_classes
#
#     def _validate(self, value, name, data):
#         for cls in self._sub_classes:
#             try:
#                 return cls._validate(self, value)
#             except TypeError:
#                 pass
#             raise TypeError('This %s property cannot accept %s.' %
#                             (self.__class__.__name__, value.__class__.__name__))

# todo: more special properties
# class Auto -> Bokeh has special prop to indicate "automatic" value
# class Date, DateTime
# class Either
# class Instance
# class Array


__all__ = []
for name, cls in list(globals().items()):
    if isinstance(cls, type) and issubclass(cls, Property):
        __all__.append(name)

del name, cls
