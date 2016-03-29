"""
Implementation of a serializer with support for custom classes. The
code is PyScript compatible; so it can also be used in JS.
"""

import json

undefined = None

class JSON:
    @staticmethod
    def parse(text, reviver=None):
        return json.loads(text, object_hook=reviver)
    @staticmethod
    def stringify(obj, replacer=None):
        return json.dumps(obj, default=replacer)


class Serializer:
    
    def __init__(self):
        self._revivers = _revivers = {}
    
        def loads(text):
            return JSON.parse(text, _reviver)
        
        def saves(obj):
            return JSON.stringify(obj, _replacer)
        
        def add_reviver(type_name, func):
            assert isinstance(type_name, str)
            _revivers[type_name] = func
        
        def _reviver(dct, val=undefined):
            if val is not undefined:  # pragma: no cover
                dct = val
            if isinstance(dct, dict):
                type = dct.get('__type__', None)
                if type is not None:
                    func = _revivers.get(type, None)
                    if func is not None:
                        return func(dct)
            return dct
        
        def _replacer(obj, val=undefined):
            if val is undefined:  # Py
                
                try:
                    return obj.__json__()  # same as in Pyramid
                except AttributeError:
                    raise TypeError('Cannot serialize object to JSON: %r' % obj)
            else:  # JS - pragma: no cover
                if (val is not None) and val.__json__ is not undefined:
                    return val.__json__()
                return val
        
        self.loads = loads
        self.saves = saves
        self.add_reviver = add_reviver


serializer = Serializer()
