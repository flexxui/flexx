"""
Test advanced component properties.
"""

from flexx.util.testing import run_tests_if_main, skipif, skip, raises
from flexx.event.both_tester import run_in_both, this_is_js

from flexx import event

loop = event.loop


class MyObject(event.Component):
    
    floatpair = event.FloatPairProp(settable=True)


@run_in_both(MyObject)
def test_property_FloatPair():
    """
    [0.0, 0.0]
    [42.0, 42.0]
    [3.2, 4.2]
    ==
    ? two values, not 3
    ? 1st value cannot be 
    ? 2nd value cannot be 
    append failed
    ----------
    [0, 0]
    [42, 42]
    [3.2, 4.2]
    ==
    ? two values, not 3
    ? 1st value cannot be
    ? 2nd value cannot be
    append failed
    """
    # We convert to list when printing, because in JS we cripple the object
    # and on Node the repr then includes the crippled methods.
    
    m = MyObject()
    print(list(m.floatpair))
    
    m.set_floatpair(42)
    loop.iter()
    print(list(m.floatpair))
    
    m.set_floatpair((3.2, 4.2))
    loop.iter()
    print(list(m.floatpair))
    
    print('==')
    
    # Fail - needs scalar or 2-tuple
    m.set_floatpair((3.2, 4.2, 1))
    loop.iter()
    
    # Fail - needs number
    m.set_floatpair(('hi', 1))
    loop.iter()
    m.set_floatpair((1, 'hi'))
    loop.iter()
    
    # Cannot append
    try:
        m.floatpair.append(9)
    except Exception:
        print('append failed')


run_tests_if_main()
