""" Tests for PyScript functions
"""

import tempfile

from pytest import raises
from flexx.util.testing import run_tests_if_main

from flexx.pyscript import js, py2js, evaljs, evalpy, JSCode, script2js, clean_code


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


def test_jscode_for_function():
    py = 'def foo(): pass'
    js = 'var foo;\nfoo = function () {\n};\n'
    f = JSCode('function', 'foo', py)
    assert f.type == 'function'
    assert f.name == 'foo'
    assert f.pycode == py
    assert f.jscode == js
    
    assert repr(f)
    assert 'function' in repr(f)
    assert py in str(f)
    assert js in str(f)
    
    # Test hash
    f2 = JSCode('function', 'foo', py)
    assert f.jshash == f2.jshash
    
    # Test renaming
    assert f.jscode_renamed('bar') == 'var bar;\nbar = function () {\n};\n'
    assert f.jscode_renamed('x.y') == 'x.y = function () {\n};\n'
    


def test_jscode_for_class():
    py = 'class Foo: pass'
    js = 'var Foo;\nFoo = function () {\n'
    f = JSCode('class', 'Foo', py)
    assert f.type == 'class'
    assert f.name == 'Foo'
    assert f.pycode == py
    assert f.jscode.startswith(js)
    
    assert repr(f)
    assert 'class' in repr(f)
    assert py in str(f)
    assert js in str(f)
    
    # Test renaming
    assert f.jscode_renamed('Bar').startswith('var Bar;\nBar = function () {\n')
    assert 'Foo' not in f.jscode_renamed('Bar')
    assert f.jscode_renamed('x.Bar').startswith('x.Bar = function () {\n')
    assert 'Foo' not in f.jscode_renamed('x.Bar')


def test_js_decorator_for_function():
    
    @js
    def foo():
        pass
    
    def bar():
        pass
    
    bar_js = js(bar)
    
    # js produces a JSCode object
    assert isinstance(foo, JSCode)
    assert isinstance(bar_js, JSCode)
    
    # Applying js twice has no effect
    assert js(foo) == foo
    
    # JSCode objects cannot be called
    raises(RuntimeError, foo)
    raises(RuntimeError, bar_js)
    raises(RuntimeError, foo, 1, 2, bar=3)
    
    raises(ValueError, js, "foo")
    raises(ValueError, js, isinstance)  # buildins are not FunctionType


def test_js_decorator_for_class():
    
    @js
    class XFoo1:
        pass
    class XFoo2:
        pass
    
    Foo_js = js(XFoo2)
    
    # js produces a JSCode object
    assert isinstance(XFoo1, JSCode)
    assert isinstance(Foo_js, JSCode)
    
    # Applying js twice has no effect
    assert js(XFoo1) == XFoo1
    
    # JSCode objects cannot be called
    raises(RuntimeError, XFoo1)
    raises(RuntimeError, Foo_js)
    raises(RuntimeError, XFoo1, 1, 2, bar=3)
    
    raises(ValueError, js, "foo")
    raises(ValueError, js, str)  # buildins fail


def test_name_mangling():
    @js
    def foo__js():
        pass
    
    @js
    def _js_bar():
        pass
    
    assert foo__js.name == 'foo'
    assert _js_bar.name == '_bar'


def test_raw_js():
    
    @js
    def func(a, b):
        """
        var c = 3;
        return a + b + c;
        """
    
    code = func.jscode
    assert evaljs(code + 'func(100, 10)') == '113'
    assert evaljs(code + 'func("x", 10)') == 'x103'


TEST_CODE = """

var foo = function () {};

var foo = function () {};

var f1;
f1 = function () {
    var foo = function () {};
    var bar = function () {};
}

var f2;
f2 = function () {
    var foo = function () {};
    var bar = function () {};
}
"""

def test_clean_code():
    
    code = clean_code(TEST_CODE)
    assert code.count('var foo =') == 1
    assert code.count('var bar =') == 2


def test_scripts():
    # Prepare
    pycode = 'foo = 42; print(foo)'
    f = tempfile.NamedTemporaryFile('wt', suffix='.py')
    f.file.write(pycode)
    f.file.flush()
    jsname = f.name[:-3] + '.js'
    
    # Convert - plain file (no module)
    script2js(f.name)
    
    # Check result
    jscode = open(jsname, 'rt').read()
    assert 'foo = 42;' in jscode
    assert 'define(' not in jscode
    
    # Convert - module
    script2js(f.name, 'mymodule')
    
    # Check result
    jscode = open(jsname, 'rt').read()
    assert 'foo = 42;' in jscode
    assert 'define(' in jscode
    assert 'module.exports' in jscode
    assert 'root.mymodule' in jscode
    
    # Convert - no module, explicit file
    script2js(f.name, None, jsname)
    
    # Check result
    jscode = open(jsname, 'rt').read()
    assert 'foo = 42;' in jscode
    assert 'define(' not in jscode


run_tests_if_main()
