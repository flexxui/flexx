""" Tests for PyScript functions
"""

import os
import tempfile

from pytest import raises
from flexx.util.testing import run_tests_if_main

from flexx.pyscript import py2js, evaljs, evalpy, script2js, stdlib


def test_py2js_on_wrong_vals():
    
    raises(ValueError, py2js, [])
    raises(ValueError, py2js, {})
    
    raises(ValueError, py2js, str)  # cannot find source for str


def test_py2js_on_strings():
    # No need for extensive testing; we use this function extensively
    # in the other tests ...
    assert py2js('3 + 3') == '3 + 3;'
    assert py2js('list()') == '[];'

def test_stdlib():
    code = stdlib.get_full_std_lib()
    assert isinstance(code, str)
    assert 'var py_hasattr =' in code
    assert 'var py_list =' in code
    assert code.count('var') > 10
    
    code = stdlib.get_partial_std_lib(['hasattr'], [])
    assert isinstance(code, str)
    assert 'var py_hasattr =' in code
    assert 'var py_list =' not in code
    assert code.count('var') == 1
    
    assert 'py_hasattr = function' in py2js('hasattr(x, "foo")')
    assert 'py_hasattr = function' not in py2js('hasattr(x, "foo")', inline_stdlib=False)

def test_evaljs():
    assert evaljs('3+4') == '7'
    assert evaljs('x = {}; x.doesnotexist') == ''  # strip undefined


def test_evalpy():
    assert evalpy('[3, 4]') == '[ 3, 4 ]'
    assert evalpy('[3, 4]', False) == '[3,4]'


def test_py2js_on_function():
    
    def foo():
        pass
    
    # normal
    jscode = py2js(foo)
    assert jscode.startswith('var foo')
    assert jscode.pycode.startswith('def foo')
    
    # renamed
    jscode = py2js(foo, 'bar')
    assert jscode.pycode.startswith('def foo')
    assert 'foo' not in jscode
    assert jscode.startswith('var bar')
    assert 'bar = function ' in jscode
    
    # renamed 2
    jscode = py2js(foo, 'bar.bla')
    assert jscode.pycode.startswith('def foo')
    assert 'foo' not in jscode
    assert not 'var bar.bla' in jscode
    assert 'bar.bla = function ' in jscode
    
    
    # Skip decorators
    stub1 = lambda x: x
    stub2 = lambda x=None: stub1
    
    @stub1
    @stub1
    def foo1():
        pass
    
    @stub2(
    )
    def foo2():
        pass
    
    @py2js
    def foo3():
        pass
    
    @py2js(indent=1)
    def foo4():
        pass
    
    assert callable(foo1)
    assert callable(foo2)
    assert py2js(foo1).pycode.startswith('def foo')
    assert py2js(foo2).pycode.startswith('def foo')
    assert foo3.startswith('var foo3')
    assert foo4.startswith('    var foo4')


def test_py2js_on_class():
    
    class Foo1:
        X = 3
        def spam():
            pass
    
    # normal
    jscode = py2js(Foo1)
    assert jscode.startswith('var Foo1')
    assert jscode.pycode.startswith('class Foo1')
    
    # renamed
    jscode = py2js(Foo1, 'Bar')
    assert jscode.pycode.startswith('class Foo')
    assert 'Foo' not in jscode
    assert jscode.startswith('var Bar')
    
    # renamed 2
    jscode = py2js(Foo1, 'Bar.bla')
    assert jscode.pycode.startswith('class Foo')
    assert 'Foo' not in jscode
    assert not 'var Bar.bla' in jscode
    assert 'Bar.bla = function ' in jscode


def test_raw_js():
    
    def func(a, b):
        """
        var c = 3;
        return a + b + c;
        """
    
    code = py2js(func)
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

# def test_clean_code():
#     
#     code = clean_code(TEST_CODE)
#     assert code.count('var foo =') == 1
#     assert code.count('var bar =') == 2


def test_scripts():
    # Prepare
    pycode = 'foo = 42; print(foo)'
    pyname = os.path.join(tempfile.gettempdir(), 'flexx_test.py')
    with open(pyname, 'wb') as f:
        f.write(pycode.encode())
    jsname = pyname[:-3] + '.js'
    
    # Convert - plain file (no module)
    script2js(pyname)
    
    # Check result
    jscode = open(jsname, 'rt', encoding='utf-8').read()
    assert 'foo = 42;' in jscode
    assert 'define(' not in jscode
    
    # Convert - module
    script2js(pyname, 'mymodule')
    
    # Check result
    jscode = open(jsname, 'rt', encoding='utf-8').read()
    assert 'foo = 42;' in jscode
    assert 'define(' in jscode
    assert 'module.exports' in jscode
    assert 'root.mymodule' in jscode
    
    # Convert - no module, explicit file
    script2js(pyname, None, jsname)
    
    # Check result
    jscode = open(jsname, 'rt', encoding='utf-8').read()
    assert 'foo = 42;' in jscode
    assert 'define(' not in jscode


run_tests_if_main()
