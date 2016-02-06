"""
Most of the stuff from the stdlib will be tested via test_parser3. That
will mostly test if the implemenation is correct. This module does some
meta tests.
"""

import sys

from flexx.util.testing import run_tests_if_main, raises

from flexx.pyscript import py2js, evaljs, evalpy, Parser3, stdlib


def test_stdlib_full_and_partial():
    code = stdlib.get_full_std_lib()
    assert isinstance(code, str)
    assert 'var %shasattr =' % stdlib.FUNCTION_PREFIX in code
    assert 'var %slist =' % stdlib.FUNCTION_PREFIX in code
    assert code.count('var') > 10
    
    code = stdlib.get_partial_std_lib(['hasattr'], [], []) 
    assert isinstance(code, str)
    assert 'var %shasattr =' % stdlib.FUNCTION_PREFIX in code
    assert 'var %slist =' % stdlib.FUNCTION_PREFIX not in code
    assert code.count('var') == 1
    
    assert '_hasattr = function' in py2js('hasattr(x, "foo")')
    assert '_hasattr = function' not in py2js('hasattr(x, "foo")', inline_stdlib=False)

def test_stdlib_has_all_list_methods():
    method_names = [m for m in dir(list) if not m.startswith('_')]
    for method_name in method_names:
        assert method_name in stdlib.METHODS

def test_stdlib_has_all_dict_methods():
    method_names = [m for m in dir(dict) if not m.startswith('_')]
    if sys.version_info[0] == 2:
        ignore = 'fromkeys has_key viewitems viewkeys viewvalues iteritems iterkeys itervalues'
    else:
        ignore = 'fromkeys'
    for name in ignore.split(' '):
        method_names.remove(name)
    for method_name in method_names:
        assert method_name in stdlib.METHODS

def test_stdlib_has_all_str_methods():
    method_names = [m for m in dir(str) if not m.startswith('_')]
    if sys.version_info[0] == 2:
        ignore = 'encode decode format isdigit'
    else:
        ignore = 'encode format format_map isdecimal isdigit isprintable maketrans'
    for name in ignore.split(' '):
        method_names.remove(name)
    for method_name in method_names:
        assert method_name in stdlib.METHODS

run_tests_if_main()
