"""
Most of the stuff from the stdlib will be tested via test_parser3. That
will mostly test if the implemenation is correct. This module does some
meta tests.
"""

from pytest import raises
from flexx.util.testing import run_tests_if_main

from flexx.pyscript import py2js, evaljs, evalpy, Parser3, stdlib


def test_stdlib_full_and_partial():
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


def test_stdlib_has_all_list_methods():
    method_names = [m for m in dir(list) if not m.startswith('_')]
    parser_names = dir(Parser3)
    for method_name in method_names:
        assert method_name in stdlib.METHODS
        assert ('method_' + method_name) in parser_names


run_tests_if_main()
