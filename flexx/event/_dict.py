"""
Implementation of a dict class with attribute access.
"""

import re

try:  # pragma: no cover
    from collections import OrderedDict as _dict
except ImportError:
    _dict = dict


def isidentifier(s):
    # http://stackoverflow.com/questions/2544972/
    if not isinstance(s, str):
        return False
    return re.match(r'^\w+$', s, re.UNICODE) and re.match(r'^[0-9]', s) is None


class Dict(_dict):
    """ A dict in which the items can be get/set as attributes.

    This provides a lean way to represent structured data, and works
    well in combination with autocompletion. Keys can be anything that
    are otherwise valid keys, but keys that are not valid identifiers
    or that are methods of the dict class (e.g. 'items' or 'copy')
    can only be get/set in the classic way.

    Example:

    .. code-block:: python

        >> d = Dict(foo=3)
        >> d.foo
        3
        >> d['foo'] = 4
        >> d.foo
        4
        >> d.bar = 5
        >> d.bar
        5

    """

    __reserved_names__ = dir(_dict())  # Also from OrderedDict
    __pure_names__ = dir(dict())

    __slots__ = []

    def __repr__(self):
        identifier_items = []
        nonidentifier_items = []
        for key, val in self.items():
            if isidentifier(key):
                identifier_items.append('%s=%r' % (key, val))
            else:
                nonidentifier_items.append('(%r, %r)' % (key, val))
        if nonidentifier_items:
            return 'Dict([%s], %s)' % (', '.join(nonidentifier_items),
                                       ', '.join(identifier_items))
        else:
            return 'Dict(%s)' % (', '.join(identifier_items))

    def __getattribute__(self, key):
        try:
            return object.__getattribute__(self, key)
        except AttributeError:
            if key in self:
                return self[key]
            else:
                raise

    def __setattr__(self, key, val):
        if key in Dict.__reserved_names__:
            # Either let OrderedDict do its work, or disallow
            if key not in Dict.__pure_names__:  # pragma: no cover
                return _dict.__setattr__(self, key, val)
            else:
                raise AttributeError('Reserved name, this key can only ' +
                                     'be set via ``d[%r] = X``' % key)
        else:
            # if isinstance(val, dict): val = Dict(val) -> no, makes a copy!
            self[key] = val

    def __dir__(self):
        names = [k for k in self.keys() if isidentifier(k)]
        return Dict.__reserved_names__ + names
