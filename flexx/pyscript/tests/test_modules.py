""" Tests for functionality to create JS modules.

Note that some tests in func also implicitly test this.
"""

import os
import tempfile

from flexx.util.testing import run_tests_if_main, raises

from flexx.pyscript.modules import create_js_module


CODE = """
foo = 3
bar = 4
"""


def test_js_module_types():
    
    code = create_js_module('baz.js', CODE, ['bb'], 'aa', 'hidden')
    assert 'define' not in code
    assert 'require' not in code
    assert 'bb' not in code
    assert 'aa' not in code
    assert 'return' not in code
    
    code = create_js_module('baz.js', CODE, ['bb'], 'aa', 'simple')
    assert 'define' not in code
    assert 'require' not in code
    assert 'bb' not in code
    assert 'return aa' in code

    code = create_js_module('baz.js', CODE, ['bb'], 'aa', 'amd')
    assert 'define' in code
    assert 'require' not in code
    assert 'bb' in code
    assert 'return aa' in code

    code = create_js_module('baz.js', CODE, ['bb'], 'aa', 'umd')
    assert 'define' in code
    assert 'require' in code
    assert 'bb' in code
    assert 'return aa' in code
    
    with raises(ValueError):  # type not a str
        create_js_module('baz.js', CODE, ['bb'], 'aa', 3)
    
    with raises(ValueError):  # invalid type
        create_js_module('baz.js', CODE, ['bb'], 'aa', 'not_known')


def test_js_module_names():
    
    with raises(ValueError):  # name not a str
        create_js_module(3, CODE, ['bb'], 'aa', 'simple')
    
    with raises(ValueError):  # name empty str
        create_js_module('', CODE, ['bb'], 'aa', 'simple')
    
    code = create_js_module('foo.js', CODE, ['bb'], 'aa', 'simple')
    assert '.foo =' in code  # using safe names


def test_js_module_code():
    with raises(ValueError):  # code not a str
        create_js_module('foo.js', 4, ['bb'], 'aa', 'simple')


def test_js_module_imports():
    with raises(ValueError):  # imports not a list
        create_js_module('foo.js', CODE, 'bb', 'aa', 'simple')
    
    with raises(ValueError):  # imports element not a str
        create_js_module('foo.js', CODE, ['bb', 4], 'aa', 'simple')
    
    for type in ('amd', 'umd'):
        code = create_js_module('foo.js', CODE, ['bb as cc', 'dd'], 'aa', type)
        assert '"bb"' in code
        assert '"dd"' in code
        assert '"cc"' not in code
        assert 'cc, dd' in code


def test_js_module_exports():
    with raises(ValueError):  # exports not a str or list
        create_js_module('foo.js', CODE, ['bb'], 3, 'simple')
    with raises(ValueError):  # exports element not a str
        create_js_module('foo.js', CODE, ['bb'], ['aa', 3], 'simple')
    
    code =create_js_module('foo.js', CODE, ['bb'], 'aa', 'simple')
    assert 'return aa' in code
    
    code = create_js_module('foo.js', CODE, ['bb'], ['aa', 'bb'], 'simple')
    assert 'return {aa: aa, bb: bb}' in code
    
    

run_tests_if_main()
