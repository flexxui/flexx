from flexx.util.testing import run_tests_if_main, raises

from flexx.pyscript.parser0 import JSError, unify
from flexx import pyscript


def test_unify():
    
    # Simple objects
    assert unify('3') == '3'
    assert unify('3.12') == '3.12'
    assert unify('"aa"') == '"aa"'
    assert unify("'aa'") == "'aa'"
    
    # Simple names
    assert unify('foo') == 'foo'
    assert unify('foo.bar') == 'foo.bar'
    assert unify('foo_12') == 'foo_12'
    
    # Simple calls
    assert unify('foo()') == 'foo()'
    assert unify('bar.fo_o()') == 'bar.fo_o()'
    
    # Anything that already has braces or []
    assert unify('(foo)') == '(foo)'
    assert unify('(3 + 3)') == '(3 + 3)'
    assert unify('[2, 3]') == '[2, 3]'
    
    # Func calls with args (but no extra braces)
    assert unify('xxxxx(some args bla)') == 'xxxxx(some args bla)'
    assert unify('foo(3)') == 'foo(3)'
    
    # Indexing
    assert unify('foo[1]') == 'foo[1]'
    assert unify('bar.foo[1:2,3]') == 'bar.foo[1:2,3]'
    
    # Dict
    assert unify('{a:3, b:"5"}') == '{a:3, b:"5"}'
    
    # Otherwise ... braces!
    assert unify('3+3') == '(3+3)'
    assert unify('(3)+(3)') == '((3)+(3))'
    assert unify('[3]+[3]') == '([3]+[3])'
    assert unify('foo((3))') == '(foo((3)))'
    assert unify('bar+foo(3)') == '(bar+foo(3))'
    assert unify('b + {a:3}') == '(b + {a:3})'


run_tests_if_main()
