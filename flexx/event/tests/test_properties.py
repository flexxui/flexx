"""
Test component properties.
"""

from flexx.util.testing import run_tests_if_main, skipif, skip, raises
from flexx.event.both_tester import run_in_both, this_is_js

from flexx import event

loop = event.loop


class MyCustomProp(event.Property):

    _default = 'a'

    def _validate(self, value, name, data):
        if value not in 'abc':
            raise TypeError('MyCustomProp must have a value of "a", "b", or "c".')
        return value


class MyObject(event.Component):

    att = event.Attribute()

    # Props to test basic stuff
    foo = event.AnyProp(6, settable=True, doc='can be anything')
    bar = event.StringProp('xx')  # not settable

    # Props to test array mutations
    eggs = event.ListProp([], settable=True)
    eggs2 = event.ListProp(settable=True)
    eggs3 = event.ListProp([3, 4])

    # All kinds of props, defaults
    anyprop = event.AnyProp(doc='can be anything', settable=True)
    boolprop = event.BoolProp(settable=True)
    tristateprop = event.TriStateProp(settable=True)
    intprop = event.IntProp(settable=True)
    floatprop = event.FloatProp(settable=True)
    stringprop = event.StringProp(settable=True)
    tupleprop = event.TupleProp(settable=True)
    listprop = event.ListProp(settable=True)
    dictprop = event.DictProp(settable=True)
    componentprop = event.ComponentProp(settable=True)  # can be None
    # nullprop = event.NullProp(None, settable=True)
    # eitherprop = event.EitherProp(event.IntProp, event.NoneProp)
    _privateprop = event.IntProp(settable=True)


class MyObjectWithCustom(event.Component):
    myprop1 = MyCustomProp(settable=True)
    myprop2 = MyCustomProp('b', settable=True)


@run_in_both(MyObject)
def test_property_setting():
    """
    6
    xx
    6
    3.2
    fail ok
    xx
    """

    m = MyObject()
    print(m.foo)
    print(m.bar)

    m.set_foo(3.2)
    print(m.foo)
    loop.iter()
    print(m.foo)

    try:
        m.set_bar('yy')
    except AttributeError:
        print('fail ok')  # py
    except TypeError:
        print('fail ok')  # js
    print(m.bar)


@run_in_both(MyObject)
def test_private_property():
    """
    0
    0
    3
    """

    m = MyObject()
    print(m._privateprop)

    m._set_privateprop(3)
    print(m._privateprop)
    loop.iter()
    print(m._privateprop)


@run_in_both(MyObject)
def test_property_mutating():
    """
    cannot mutate
    6
    9
    """
    m = MyObject()

    try:
        m._mutate_foo(9)
    except AttributeError:
        print('cannot mutate')

    print(m.foo)

    # Hack
    loop._processing_action = True
    m._mutate_foo(9)
    print(m.foo)


@run_in_both(MyObject)
def test_property_defaults1():
    """
    9
    xx
    9
    xx
    yy
    fail ok
    end
    """

    m = MyObject(foo=9)
    print(m.foo)
    print(m.bar)

    loop.iter()
    print(m.foo)
    print(m.bar)

    # Even non-settable props can be initialized at instantiation
    # try:
    #     MyObject(bar='yy')
    # except TypeError:
    #     print('fail ok')  # py and js
    m = MyObject(bar='yy')
    print(m.bar)

    # But need settable prop if setting to implicit reaction
    try:
        MyObject(bar=lambda:'yy')
    except TypeError:
        print('fail ok')  # py and js

    print('end')


@run_in_both(MyObject)
def test_property_list_init():
    """
    []
    [3, 4]
    []
    [7, 8, 9]
    """
    m = MyObject()
    print(m.eggs)
    print(m.eggs3)

    # Good auto-defaults
    print(m.eggs2)

    m = MyObject(eggs=[7,8,9])
    loop.iter()
    print(m.eggs)


@run_in_both(MyObject)
def test_property_list_mutate():
    """
    []
    [1, 2, 3, 4, 5, 6, 7, 8]
    [1, 2, 3, 44, 55, 66, 7, 8]
    [1, 2, 3, 7, 8]
    fail IndexError
    """
    m = MyObject()
    print(m.eggs)

    loop._processing_action = True

    m._mutate_eggs([5, 6], 'insert', 0)
    m._mutate_eggs([1, 2], 'insert', 0)
    m._mutate_eggs([3, 4], 'insert', 2)
    m._mutate_eggs([7, 8], 'insert', 6)
    print(m.eggs)

    m._mutate_eggs([44, 55, 66], 'replace', 3)
    print(m.eggs)

    m._mutate_eggs(3, 'remove', 3)
    print(m.eggs)

    try:
        m._mutate_eggs([7, 8], 'insert', -1)
    except IndexError:
        print('fail IndexError')


@run_in_both(MyObject)
def test_property_dict_mutate():
    """
    {}
    {bar: 4, foo: 3}
    {bar: 4, foo: 5}
    {bar: 4}
    fail IndexError
    """
    m = MyObject()
    print(m.dictprop)

    loop._processing_action = True

    m._mutate_dictprop(dict(foo=3), 'insert')
    m._mutate_dictprop(dict(bar=4), 'replace')  # == insert

    print('{' + ', '.join(['%s: %i' % (key, val)
                          for key, val in sorted(m.dictprop.items())]) + '}')

    m._mutate_dictprop(dict(foo=5), 'replace')
    print('{' + ', '.join(['%s: %i' % (key, val)
                          for key, val in sorted(m.dictprop.items())]) + '}')


    m._mutate_dictprop(['foo'], 'remove')
    print('{' + ', '.join(['%s: %i' % (key, val)
                          for key, val in sorted(m.dictprop.items())]) + '}')

    try:
       m._mutate_dictprop(dict(foo=3), 'insert', 0)
    except IndexError:
        print('fail IndexError')


@run_in_both(MyObject)
def test_property_persistance1():  # anyprop just sets, listProm makes a copy
    """
    []
    []
    [3, 4]
    []
    """
    m = MyObject()
    x = []
    m.set_foo(x)
    m.set_eggs(x)
    loop.iter()

    print(m.foo)
    print(m.eggs)

    x.extend([3, 4])
    print(m.foo)
    print(m.eggs)


@run_in_both(MyObject)
def test_property_persistance2():  # now we use the egg prop value itself
    """
    []
    []
    [3, 4]
    []
    """
    m = MyObject()
    x = m.eggs  # <-- only difference (previously, updating x affected eggs. Not anymore.
    m.set_foo(x)
    m.set_eggs(x)
    loop.iter()

    print(m.foo)
    print(m.eggs)

    x.extend([3, 4])
    print(m.foo)
    print(m.eggs)


## Defaults and overloading/inheritance


class MyDefaults(event.Component):
    # Custom defaults
    anyprop2 = event.AnyProp(7, doc='can be anything')
    boolprop2 = event.BoolProp(True)
    intprop2 = event.IntProp(-9)
    floatprop2 = event.FloatProp(800.45)
    stringprop2 = event.StringProp('heya')
    tupleprop2 = event.TupleProp((2, 'xx'))
    listprop2 = event.ListProp([3, 'yy'])
    dictprop2 = event.DictProp({'foo':3, 'bar': 4})
    componentprop2 = event.ComponentProp(None)


class MyDefaults2(MyDefaults):
    floatprop2 = event.FloatProp(3.14)
    stringprop2 = event.StringProp('hi')


@run_in_both(MyDefaults)
def test_property_defaults2():
    """
    7
    True
    -9
    800.45
    heya
    [True, 2, 'xx']
    [3, 'yy']
    {bar: 4, foo: 3}
    True
    """
    m = MyDefaults()
    print(m.anyprop2)
    print(m.boolprop2)
    print(m.intprop2)
    print(m.floatprop2)
    print(m.stringprop2)
    print([isinstance(m.tupleprop2, tuple)] + list(m.tupleprop2))  # grrr
    print(m.listprop2)
    print('{' + ', '.join(['%s: %i' % (key, val)
                          for key, val in sorted(m.dictprop2.items())]) + '}')
    print(m.componentprop2 is None)


@run_in_both(MyDefaults2)
def test_property_defaults3():
    """
    3.14
    hi
    7
    """
    m = MyDefaults2()
    # From overloaded class
    print(m.floatprop2)
    print(m.stringprop2)
    # From base class
    print(m.anyprop2)


@run_in_both(MyObjectWithCustom, MyCustomProp)
def test_property_defaults4():
    """
    a
    b
    """
    m = MyObjectWithCustom()
    print(m.myprop1)
    print(m.myprop2)


## All prop types


@run_in_both(MyObject)
def test_property_any():  # Can be anything
    """
    True
    42
    ? Loop
    """
    m = MyObject()
    print(m.anyprop is None)  # Because None becomes null in JS

    m.set_anyprop(42)
    loop.iter()
    print(m.anyprop)

    m.set_anyprop(loop)
    loop.iter()
    print(m.anyprop)


@run_in_both(MyObject)
def test_property_bool():  # Converts to bool, no type checking
    """
    False
    True
    False
    True
    """
    m = MyObject()
    print(m.boolprop)

    m.set_boolprop(42)
    loop.iter()
    print(m.boolprop)

    m.set_boolprop('')
    loop.iter()
    print(m.boolprop)

    m.set_boolprop(loop)
    loop.iter()
    print(m.boolprop)


@run_in_both(MyObject)
def test_property_tristate():  # Converts to bool, no type checking
    """
    None
    True
    False
    None
    """
    m = MyObject()
    print(m.tristateprop)

    m.set_tristateprop(42)
    loop.iter()
    print(m.tristateprop)

    m.set_tristateprop('')
    loop.iter()
    print(m.tristateprop)

    m.set_tristateprop(None)
    loop.iter()
    print(m.tristateprop)


@run_in_both(MyObject)
def test_property_int():  # typechecking, but converts from float/str
    """
    0
    42
    9
    ? TypeError
    9
    """
    m = MyObject()
    print(m.intprop)

    m.set_intprop(42.9)
    loop.iter()
    print(m.intprop)

    m.set_intprop('9')  # actually, '9.1' would fail on Python
    loop.iter()
    print(m.intprop)

    m.set_intprop(loop)  # fail
    loop.iter()
    print(m.intprop)


@run_in_both(MyObject)
def test_property_float():  # typechecking, but converts from int/str
    """
    ? 0
    42.9
    9.1
    ? TypeError
    9.1
    """
    m = MyObject()
    print(m.floatprop)

    m.set_floatprop(42.9)
    loop.iter()
    print(m.floatprop)

    m.set_floatprop('9.1')  # actually, '9.1' would fail on Python
    loop.iter()
    print(m.floatprop)

    m.set_floatprop(loop)  # fail
    loop.iter()
    print(m.floatprop)


@run_in_both(MyObject)
def test_property_string():
    """
    .

    hello
    ? TypeError
    hello
    """
    print('.')

    m = MyObject()
    print(m.stringprop)

    m.set_stringprop('hello')
    loop.iter()
    print(m.stringprop)

    m.set_stringprop(3)
    loop.iter()
    print(m.stringprop)


@run_in_both(MyObject)
def test_property_tuple():
    """
    []
    [3, 4]
    [5, 6]
    ? TypeError
    ? TypeError
    ? TypeError
    [5, 6]
    append failed
    reverse failed
    """
    # We convert to list when printing, because in JS we cripple the object
    # and on Node the repr then includes the crippled methods. This way, the
    # output for Py and JS is also the same. At the bottom we validate that
    # the value is indeed ummutable.
    m = MyObject()
    print(list(m.tupleprop))

    m.set_tupleprop((3, 4))
    loop.iter()
    print(list(m.tupleprop))

    m.set_tupleprop((5, 6))
    loop.iter()
    print(list(m.tupleprop))

    for value in [3, None, 'asd']:
        m.set_tupleprop(value)
        loop.iter()
    print(list(m.tupleprop))

    # Cannot append to a tuple
    try:
        m.tupleprop.append(9)
    except Exception:
        print('append failed')

    # Cannot reverse a tuple
    try:
        m.tupleprop.reverse()
    except Exception:
        print('reverse failed')


@run_in_both(MyObject)
def test_property_list():
    """
    []
    [3, 4]
    [5, 6]
    ? TypeError
    ? TypeError
    ? TypeError
    [5, 6]
    .
    [1, 2, 3]
    [1, 2, 3, 5]
    """
    m = MyObject()
    print(m.listprop)

    m.set_listprop((3, 4))
    loop.iter()
    print(m.listprop)

    m.set_listprop((5, 6))
    loop.iter()
    print(m.listprop)

    for value in [3, None, 'asd']:
        m.set_listprop(value)
        loop.iter()
    print(m.listprop)

    print('.')
    # copies are made on set
    x = [1, 2]
    m.set_listprop(x)
    x.append(3)  # this gets in, because copie happens at validation (i.e. mutation)
    loop.iter()
    x.append(4)  # this does not
    loop.iter()
    print(m.listprop)
    m.listprop.append(5)  # this is inplace; use tuples where we can
    print(m.listprop)


@run_in_both(MyObject)
def test_property_component():  # Can be a Component or None
    """
    True
    [False, True, False]
    [False, False, True]
    [True, False, False]
    ? TypeError
    ? TypeError
    ? TypeError
    [True, False, False]
    """
    m = MyObject()
    m1 = MyObject()
    m2 = MyObject()
    print(m.componentprop is None)

    m.set_componentprop(m1)
    loop.iter()
    print([m.componentprop is None, m.componentprop is m1, m.componentprop is m2])

    m.set_componentprop(m2)
    loop.iter()
    print([m.componentprop is None, m.componentprop is m1, m.componentprop is m2])

    m.set_componentprop(None)
    loop.iter()
    print([m.componentprop is None, m.componentprop is m1, m.componentprop is m2])

    for value in [3, loop, 'asd']:
        m.set_componentprop(value)
        loop.iter()
    print([m.componentprop is None, m.componentprop is m1, m.componentprop is m2])


@run_in_both(MyObjectWithCustom, MyCustomProp)
def test_property_custom():
    """
    a
    c
    ? TypeError
    ? TypeError
    ? TypeError
    c
    """
    m = MyObjectWithCustom()
    print(m.myprop1)

    m.set_myprop1('c')
    loop.iter()
    print(m.myprop1)

    for value in [3, loop, 'd']:
        m.set_myprop1(value)
        loop.iter()
    print(m.myprop1)


## Meta-ish tests that are similar for property/emitter/action/reaction


@run_in_both(MyObject)
def test_property_not_settable():
    """
    fail AtributeError
    """
    m = MyObject()
    try:
        m.foo = 3
    except AttributeError:
        print('fail AtributeError')

    # We cannot prevent deletion in JS, otherwise we cannot overload


def test_property_python_only():

    # Fail component needs property instance, not class
    with raises(TypeError):
        class MyObject2(event.Component):
            foo = event.AnyProp

    # Fail multiple positional args
    with raises(TypeError):
        class MyObject2(event.Component):
            foo = event.AnyProp(3, 4)

    # Fail on old syntax
    with raises(TypeError):
        class MyObject2(event.Component):
            @event.Property
            def foo(self, v):
                pass

    with raises(TypeError):
        event.AnyProp(doc=3)


    m = MyObject()

    # Check type of the instance attribute
    # -> Ha! the attrubute it the prop value!
    # assert isinstance(m.foo, event._action.Action)

    # Cannot set or delete a property
    with raises(AttributeError):
        m.foo = 3
    with raises(AttributeError):
        del m.foo

    # Repr and docs
    assert 'anything' in m.__class__.foo.__doc__
    assert 'anyprop' in repr(m.__class__.foo).lower()
    assert 'foo' in repr(m.__class__.foo).lower()
    # Also for one with defaults
    m = MyDefaults()
    assert 'anything' in m.__class__.anyprop2.__doc__
    assert 'anyprop' in repr(m.__class__.anyprop2).lower()


run_tests_if_main()
