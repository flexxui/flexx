"""
The properties module provides a system to add properties to classes,
that are validated, provide means for notification and serialization.

To use props, simply assign them as class attributes::

    class Foo(HasProps):
        size = Int(3, 'The size of the foo')
        title = Str('nameless', 'The title of the foo')

To create new props, inherit from Prop and implement ``validate()``::

    class MyProp(Prop):
        _default = None  # The default for when no default is given
        def validate(self, val):
            assert isinstance(val, int, float)  # require scalars
            return float(val)  # always store as float

Any prop can only store hashable objects. This includes tuples, provided
that the items it contains are hashable too. A prop may accept
nonhashable values (e.g. list), but the data must be stored as an
immutable object.

Need more docs.
"""

from .base import Prop, HasProps, HasPropsMeta
from .props import Bool, Int, Float, Str, Tuple, Color, Instance
