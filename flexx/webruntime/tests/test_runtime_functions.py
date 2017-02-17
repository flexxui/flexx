""" Test some loose functions
"""

from flexx.util.testing import run_tests_if_main, raises, skipif


from flexx.webruntime._manage import versionstring
from flexx.webruntime import _expand_runtime_name

def test_versionstring():
    
    # Format
    assert versionstring('10') .count('.') == 1
    assert versionstring('10.1') .count('.') == 2
    assert versionstring('10.1.2') .count('.') == 3
    
    # Ignore empty parts
    assert versionstring('10..1') == versionstring('10.1')
    assert versionstring('10....1..2') == versionstring('10.1.2')
    assert versionstring('10 . 1') == versionstring('10.1')
    
    # Allow recursion
    assert versionstring('10.1') == versionstring(versionstring('10.1'))
    
    # Simple comparisons
    assert versionstring('10') > versionstring('9')
    assert versionstring('10.1') > versionstring('9.1')
    assert versionstring('1.10') > versionstring('1.9')
    assert versionstring('10.1') > versionstring('9.9')
    assert versionstring('10.1.2.3.4.5.6') > versionstring('10.1.2.3.4.5.5')
    
    # Slightly trickier
    assert versionstring('10.1.1') > versionstring('10.1')
    assert versionstring('10.1.0') > versionstring('10.1')
    
    # Suffixes
    assert versionstring('10.1') > versionstring('10.1.a')
    assert versionstring('10.1') > versionstring('10.1a')
    assert versionstring('10.1rc1') > versionstring('10.1a')
    assert versionstring('10.1rc1') > versionstring('10.1.a')
    assert versionstring('10.1rc2') > versionstring('10.1rc1')
    
    # Latest is special
    assert versionstring('latest') > versionstring('999.999.999')



def test_expand_runtime_name():
    assert 'nw-app' in _expand_runtime_name('app')
    assert 'firefox-app' in _expand_runtime_name('app')
    

run_tests_if_main()
