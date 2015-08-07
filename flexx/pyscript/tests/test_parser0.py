from pytest import raises
from flexx.util.testing import run_tests_if_main

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
    assert unify('foo12') == 'foo12'
    
    # Simple calls
    assert unify('foo()') == 'foo()'
    assert unify('bar.foo()') == 'bar.foo()'
    
    # Anything that already has braces or []
    assert unify('(foo)') == '(foo)'
    assert unify('(3 + 3)') == '(3 + 3)'
    assert unify('[2, 3]') == '[2, 3]'
    
    # Func calls with args (but no extra braces)
    assert unify('_truthy(some args bla)') == '_truthy(some args bla)'
    assert unify('foo(3)') == 'foo(3)'
    
    # Otherwise ... braces!
    assert unify('3+3') == '(3+3)'
    assert unify('(3)+(3)') == '((3)+(3))'
    assert unify('[3]+[3]') == '([3]+[3])'
    assert unify('foo((3))') == '(foo((3)))'


run_tests_if_main()
