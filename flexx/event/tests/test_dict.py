
from flexx.util.testing import run_tests_if_main, skipif, skip, raises

from flexx import event
from flexx.event._dict import isidentifier


def test_isidentifier():

    for name in ['foo', 'bar', 'asdasdaskjdbf', 'Bar', 'FOO',  # simple
                 'fóó', 'é', 'élé',  # unicode
                 '_', '_1', '_foo', 'f_', 'k_k',  # with underscore
                 'f1', 'x0ff',  # with numbers
                 ]:
        assert isidentifier(name)

    for name in ['', '*', '(', '^',  'foo,', 'b&b',  # empty string and strange chars
                 ' ', ' 12', '', 'k k', ' foo', 'foo ', '\tf', 'f\t', ' _', # with whitespace
                 '2', '42', '2foo', '2_', '123', '0xff',  # numbers
                 3, None, [],  # not a string
                 ]:
        assert not isidentifier(name)


def test_dict_ok():

    d = event.Dict(foo=3)
    assert d.foo == 3
    assert d['foo'] == 3

    d.foo = 4
    assert d.foo == 4
    assert d['foo'] == 4

    d['foo'] = 5
    assert d.foo == 5
    assert d['foo'] == 5

    d._x = 9
    assert d._x == 9

    d.__x = 8
    assert d.__x == 8

    d.x0123 = 7
    assert d.x0123 == 7

    with raises(AttributeError):
        d.bladibla


def test_dict_keys_that_are_methods():

    d = event.Dict(foo=3)

    with raises(AttributeError):
        d.copy = 3
    d['copy'] = 3
    assert d.copy != 3
    assert d['copy'] == 3


def test_dir_and_repr():

    d = event.Dict(foo=3, bar=4)
    d.spam = 5
    d.eggs = 6

    names = dir(d)
    r = repr(d)
    for name in ['foo', 'bar', 'spam', 'eggs']:
        assert name in names
        assert ('%s=' % name) in r

    # Add a non-identifier element
    d[42] = None

    names = dir(d)
    r = repr(d)
    for name in ['foo', 'bar', 'spam', 'eggs']:
        assert name in names
        assert ('%s=' % name) in r

    assert '(42, None)' in r
    assert '42' not in names
    assert 42 not in names


run_tests_if_main()
