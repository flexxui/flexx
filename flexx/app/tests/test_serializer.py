
from flexx.util.testing import run_tests_if_main, raises

from flexx.pyscript import py2js, evaljs

from flexx.app._clientcore import Serializer, serializer


class Foo:
    def __init__(self, val):
        self.val = val
    def __json__(self):
        return {'__type__': 'Foo', 'val': self.val}
    @staticmethod
    def __from_json__(obj):
        return Foo(obj['val'])
    def __eq__(self, other):
        return self.val == other.val

class Bar:
    pass


foo1, foo2, foo3 = Foo(42), Foo(7), Foo(None)
s1 = {'a': foo1, 'b': [foo2, foo3]}
    
    
def test_python():

    serializer.add_reviver('Foo', Foo.__from_json__)
    
    text = serializer.saves(s1)
    
    s2 = serializer.loads(text)
    res = s2['a'].val + s2['b'][0].val
    
    assert res == 49
    assert s1 == s2


def test_python_wrong():
    b = Bar()
    raises(TypeError, serializer.saves, b)
    

def test_js():
    
    code = py2js(Serializer)
    code += py2js(Foo)
    
    code += 'var serializer = new Serializer();\n'
    code += 'var foo1 = new Foo(42), foo2 = new Foo(7), foo3 = new Foo(null);\n'
    code += 'var s1 = {"a": foo1, "b": [foo2, foo3]};\n'
    code += 'var text = serializer.saves(s1);\n'
    code += 'var s2 = serializer.loads(text);\n'
    code += 'text + "|" + (s2.a.val + s2.b[0].val);\n'
    
    result = evaljs(code)
    text, res = result.split('|')
    
    s3 = serializer.loads(text)
    
    assert s1 == s3
    assert res == '49'


run_tests_if_main()
