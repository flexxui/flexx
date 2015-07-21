import json

undefined = None

class JSON:
    def parse(text, reviver=None):
        return json.loads(text, object_hook=reviver)
    
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
            if val is not undefined:
                dct = val
            type = dct.get('__type__', None)
            if type is not None:
                func = _revivers.get(type, None)
                if func is not None:
                    return func(dct)
            return dct
        
        def _replacer(obj, val=undefined):
            if val is undefined:
                # Py
                try:
                    return obj.__json__()  # same as in Pyramid
                except AttributeError:
                    raise TypeError()
            else:
                # JS
                if val.__json__:
                    return val.__json__()
                return val
        
        self.loads = loads
        self.saves = saves
        self.add_reviver = add_reviver


serializer = Serializer()


if __name__ == '__main__':
    
    class Foo:
        def __init__(self, val):
            self.val = val
        def __json__(self):
            return {'__type__': 'Foo', 'val': self.val}
        def __from_json__(obj):
            return Foo(obj['val'])
        def __eq__(self, other):
            return self.val == other.val
    
    serializer.add_reviver('Foo', Foo.__from_json__)
    
    foo1 = Foo(42)
    foo2 = Foo(7)
    s1 = {'a': foo1, 'b': [foo2, foo2]}
    
    text = serializer.saves(s1)
    
    s2 = serializer.loads(text)
    
    
    from flexx.pyscript import js, evaljs
    
    code = js(Serializer).jscode
    code += js(Foo).jscode
    
    code += 'var serializer = new Serializer();\n'
    code += 'var foo1 = new Foo(42), foo2 = new Foo(7);\n'
    code += 'var s1 = {"a": foo1, "b": [foo2, foo2]};\n'
    code += 'var text = serializer.saves(s1);\n'
    code += 'var s2 = serializer.loads(text);\n'
    code += 'text + "|" + (s2.a.val + s2.b[0].val);\n'
    
    result = evaljs(code)
    js_text, js_int = result.split('|')
    s3 = serializer.loads(js_text)
    
    assert s1 == s2
    assert s1 == s3
    