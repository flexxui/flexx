try:
    from collections import OrderedDict as _dict
except ImportError:
    _dict = dict

def isidentifier(s):
    return (hasattr(s, 'isalnum') and
            s.isalnum() and s and 
            (s[0].isalpha() or s[0] == '_'))


class Dict(_dict):
    """ A dict in which the keys can be get and set as if they were
    attributes. Very convenient in combination with autocompletion.
    
    This Dict still behaves as much as possible as a normal dict, and
    keys can be anything that are otherwise valid keys. However, 
    keys that are not valid identifiers or that are names of the dict
    class (such as 'items' and 'copy') cannot be get/set as attributes.
    """
    
    __reserved_names__ = dir(_dict())  # Also from OrderedDict
    __pure_names__ = dir(dict())
    
    def __repr__(self):
        return dict.__repr__(self)
    
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
            if key not in Dict.__pure_names__:
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
