"""
Test advanced component properties.
"""

from flexx.util.testing import run_tests_if_main, skipif, skip, raises
from flexx.event.both_tester import run_in_both, this_is_js

from flexx import event

loop = event.loop


class MyObject(event.Component):

    floatpair = event.FloatPairProp(settable=True)
    enum1 = event.EnumProp(('foo', 'bar', 'spam'), settable=True)
    enum2 = event.EnumProp(('foo', 'bar', 'spam'), 'bar', settable=True)
    color = event.ColorProp('cyan', settable=True)


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


@run_in_both(MyObject)
def test_property_Enum():
    """
    FOO
    BAR
    SPAM
    FOO
    ? TypeError
    ? Invalid value for enum 'enum1': EGGS
    """
    m = MyObject()
    print(m.enum1)
    print(m.enum2)

    m = MyObject(enum1='spam')
    print(m.enum1)

    m.set_enum1('foo')
    loop.iter()
    print(m.enum1)

    m.set_enum1(3)
    loop.iter()

    m.set_enum1('eggs')
    loop.iter()


@run_in_both(MyObject)
def test_property_Color1():
    """
    #00ffff 1.0
    [0.0, 1.0, 1.0, 1.0]
    rgba(0,255,255,1)
    rgba(0,255,255,0.25)
    ----------
    #00ffff 1
    [0, 1, 1, 1]
    rgba(0,255,255,1)
    rgba(0,255,255,0.25)
    """
    m = MyObject()
    print(m.color.hex, m.color.alpha)
    print(list(m.color.t))
    print(m.color.css)
    m.set_color((0, 1, 1, 0.25))
    loop.iter()
    print(m.color.css)


@run_in_both(MyObject)
def test_property_Color2():
    """
    ? #00ffff 1
    ? #ff8800 1
    ? #f48404 1
    ? #ff8800 0.5
    ? #f48404 0.5
    xx
    ? #00ff00 1
    ? #ffff00 0.5
    xx
    ? #ffff00 1
    ? #ff00ff 1
    xx
    ? #ff0000 1
    ? #00ff00 0.5
    """
    m = MyObject()
    print(m.color.hex, m.color.alpha)

    m.set_color('#f80')
    loop.iter()
    print(m.color.hex, m.color.alpha)

    m.set_color('#f48404')
    loop.iter()
    print(m.color.hex, m.color.alpha)

    m.set_color('#f808')
    loop.iter()
    print(m.color.hex, m.color.alpha)

    m.set_color('#f4840488')
    loop.iter()
    print(m.color.hex, m.color.alpha)

    print('xx')

    m.set_color('rgb(0, 255, 0)')
    loop.iter()
    print(m.color.hex, m.color.alpha)

    m.set_color('rgba(255, 255, 0, 0.5)')
    loop.iter()
    print(m.color.hex, m.color.alpha)

    print('xx')

    m.set_color('yellow')
    loop.iter()
    print(m.color.hex, m.color.alpha)

    m.set_color('magenta')
    loop.iter()
    print(m.color.hex, m.color.alpha)

    print('xx')

    m.set_color((1, 0, 0, 1))
    loop.iter()
    print(m.color.hex, m.color.alpha)

    m.set_color((0, 1, 0, 0.5))
    loop.iter()
    print(m.color.hex, m.color.alpha)

run_tests_if_main()
# if __name__ == '__main__':
    # test_property_Enum()
