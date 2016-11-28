from flexx.util.testing import run_tests_if_main, raises

from flexx import pyscript
from flexx.pyscript import RawJS


def test_stubs():
    from flexx.pyscript.stubs import window, undefined, omgnotaname
    
    assert isinstance(window, pyscript.JSConstant)
    assert isinstance(undefined, pyscript.JSConstant)
    assert isinstance(omgnotaname, pyscript.JSConstant)


def test_raw_js():
    
    with raises(TypeError):
        RawJS()
    with raises(TypeError):
        RawJS(3)
    
    # Empty
    r1 = RawJS('')
    assert str(r1) == ''
    assert r1.get_code() == ''
    assert r1.get_code(4) == ''
    assert '0' in repr(r1)
    assert r1.__module__.endswith(__name__)
    
    # Short single line
    r2 = RawJS('require("foobar")')
    assert 'require(' in repr(r2)
    assert 'require(' in str(r2)
    assert r2.get_code().startswith('require')
    assert r2.get_code(4).startswith('    require')
    assert r2.get_code(2).startswith('  require')
    assert '\n' not in r2.get_code()
    
    # Long single line
    r2b = RawJS('require("foobar")'*10)
    assert 'require(' not in repr(r2b)
    assert '1' in repr(r2b)
    
    # Multiline, start at first line
    r3 = RawJS("""for ... {
                      yyyy  
                  }
               """)
    assert 'lines' in repr(r3)
    assert 'for ...' in str(r3)
    assert str(r3).endswith('}\n')
    assert r3.get_code().count('\n') == 3
    assert r3.get_code().startswith('for')
    assert r3.get_code(4).startswith('    for')
    assert '\n    yyyy\n' in r3.get_code(0)
    assert '\n        yyyy\n' in r3.get_code(4)
    
    # Multiline, exactly the same, but start at second line; same results
    r4 = RawJS("""
        for ... {
            yyyy  
        }
        """)
    assert 'lines' in repr(r4)
    assert 'for ...' in str(r4)
    assert str(r4).endswith('}\n')
    assert r4.get_code().count('\n') == 3
    assert r4.get_code().startswith('for')
    assert r4.get_code(4).startswith('    for')
    assert '\n    yyyy\n' in r4.get_code(0)
    assert '\n        yyyy\n' in r4.get_code(4)
    
    # Multiline, now newline at the ned
    r5 = RawJS("""
        for ... {
            yyyy  
        }""")
    assert r5.get_code().count('\n') == 2
    assert str(r5).endswith('}')


run_tests_if_main()
