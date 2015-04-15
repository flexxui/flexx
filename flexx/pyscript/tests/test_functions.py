""" Tests for PyScript functions
"""

from pytest import raises
from flexx.util.testing import run_tests_if_main

from flexx.pyscript import js, py2js, evaljs, evalpy, JSFunction
from flexx import pyscript


def test_py2js():
    # No need for extensive testing; we use this function extensively
    # in the other tests ...
    assert py2js('3 + 3') == '3 + 3;'


def test_evaljs():
    assert evaljs('3+4') == '7'
    assert evaljs('x = {}; x.doesnotexist') == ''  # strip undefined


def test_evalpy():
    assert evalpy('[3, 4]') == '[ 3, 4 ]'
    assert evalpy('[3, 4]', False) == '[3,4]'


def test_jsfunction_class():
    py = 'def foo(): pass'
    js = 'function () {\n};'
    f = JSFunction('foo', py)
    assert f.name == 'foo'
    assert f.pycode == py
    assert f.jscode == js
    
    assert repr(f)
    assert py in str(f)
    assert js in str(f)


def test_js_decorator():
    
    @js
    def foo():
        pass
    
    def bar():
        pass
    
    bar_js = js(bar)
    
    # js produces a JSFunction object
    assert isinstance(foo, JSFunction)
    assert isinstance(bar_js, JSFunction)
    
    # Applying js twice has no effect
    assert js(foo) == foo
    
    # JSFunction objects cannot be called
    raises(RuntimeError, foo)
    raises(RuntimeError, bar_js)
    raises(RuntimeError, foo, 1, 2, bar=3)
    
    raises(ValueError, js, "foo")
    raises(ValueError, js, str)  # classes can be called, but are not funcs


def test_name_mangling():
    @js
    def foo__js():
        pass
    
    def bar__js():
        pass
    
    bar_js = js(bar__js)
    
    assert foo__js.name == 'foo'
    assert bar_js.name == 'bar'


def test_raw_js():
    
    @js
    def func(a, b):
        """ 
        var c = 3;
        return a + b + c;
        """
    
    code = 'var x = ' + func.jscode
    assert evaljs(code + 'x(100, 10)') == '113'
    assert evaljs(code + 'x("x", 10)') == 'x103'


run_tests_if_main()
