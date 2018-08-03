from flexx.util.testing import raises, run_tests_if_main

import os
import sys
import tempfile

from flexx.util.config import Config


SAMPLE1 = """

foo = yes
bar = 3
spam = 2.3
eggs = bla bla

[other]
bar = 9

"""

SAMPLE2 = """

[testconfig]

foo = yes
bar = 4
spam = 3.3
eggs = bla bla bla

[other]
bar = 9

"""

SAMPLE3 = """

<bullocks

:: -=

"""


def test_config_name():

    # Empty config
    c = Config('aa')
    assert len(c) == 0

    # ok
    c = Config('AA')

    with raises(TypeError):
        Config()

    with raises(ValueError):
        Config(3)

    with raises(ValueError):
        Config('0aa')

    with raises(ValueError):
        Config('_aa')


def test_defaults():

    c = Config('testconfig',
               x01=(3, int, 'an int'),
               x02=(3, float, 'a float'),
               x03=('yes', bool, 'a bool'),
               x04=((1,2,3), str, 'A list of ints, as a string'),
               x05=((1,2,3), (int, ), 'A list of ints, as a tuple'),
               x06=((1,2,3), (str, ), 'A list of strings, as a tuple'),
               )

    # Test iteration
    assert len(c) == 6
    for name in c:
        assert name in ('x01', 'x02', 'x03', 'x04', 'x05', 'x06')
    assert set(dir(c)) == set([name for name in c])

    # Test values
    assert c.x01 == 3
    assert c.x02 == 3.0
    assert c.x03 == True
    assert c.x04 == '(1, 2, 3)'
    assert c.x05 == (1, 2, 3)
    assert c.x06 == ('1', '2', '3')

    # Test docstring (e.g. alphabetic order)
    i1 = c.__doc__.find('x01')
    i2 = c.__doc__.find('x02')
    i3 = c.__doc__.find('x03')
    i4 = c.__doc__.find('x04')
    assert i1 > 0
    assert i2 > i1
    assert i3 > i2
    assert i4 > i3
    assert 'x01 (int): ' in c.__doc__
    assert 'x04 (str): ' in c.__doc__
    assert 'x05 (int-tuple): ' in c.__doc__
    assert 'x06 (str-tuple): ' in c.__doc__


def test_option_spec_fail():

    # ok
    Config('aa', foo=(3, int, ''))

    with raises(ValueError):
        Config('aa', _foo=(3, int, ''))

    for spec in [(),  # too short
                  (3, int),  # still too short
                  (3, int, 'docs', None),  # too long
                  (3, None, 'docs'),  # type is not a type
                  ('', set, 'docs'),  # type is not supported
                  ('3,3', [], 'docs'),  # tuple type needs one element
                  ('3,3', [int, int], 'docs'),  # not two
                  ('3,3', [set], 'docs'),  # and must be supported
                 ]:
        with raises(ValueError):
            Config('aa', foo=spec)


def test_read_file():

    # Prepare config files
    filename1 = os.path.join(tempfile.gettempdir(), 'flexx_config_test1.cfg')
    with open(filename1, 'wb') as f:
        f.write(SAMPLE1.encode())
    filename2 = os.path.join(tempfile.gettempdir(), 'flexx_config_test2.cfg')
    with open(filename2, 'wb') as f:
        f.write(SAMPLE2.encode())
    filename3 = os.path.join(tempfile.gettempdir(), 'flexx_config_test3.cfg')
    with open(filename3, 'wb') as f:
        f.write(SAMPLE3.encode())
    filename4 = os.path.join(tempfile.gettempdir(), 'flexx_config_test4.cfg')
    with open(filename4, 'wb') as f:
        f.write(b'\x00\xff')

    # Config without sources
    c = Config('testconfig',
               foo=(False, bool, ''), bar=(1, int, ''),
               spam=(0.0, float, ''), eggs=('', str, ''))
    assert c.foo == False
    assert c.bar == 1

    # Config with filename, implicit section
    c = Config('testconfig', filename1,
               foo=(False, bool, ''), bar=(1, int, ''),
               spam=(0.0, float, ''), eggs=('', str, ''))
    assert c.foo == True
    assert c.bar == 3
    assert c.eggs == 'bla bla'

    # Config with filename, explicit section
    c = Config('testconfig', filename2,
               foo=(False, bool, ''), bar=(1, int, ''),
               spam=(0.0, float, ''), eggs=('', str, ''))
    assert c.foo == True
    assert c.bar == 4
    assert c.eggs == 'bla bla bla'

    # Config with string, implicit section
    c = Config('testconfig', SAMPLE1,
               foo=(False, bool, ''), bar=(1, int, ''),
               spam=(0.0, float, ''), eggs=('', str, ''))
    assert c.foo == True
    assert c.bar == 3
    assert c.eggs == 'bla bla'

    # Config with string, explicit section
    c = Config('testconfig', SAMPLE2,
               foo=(False, bool, ''), bar=(1, int, ''),
               spam=(0.0, float, ''), eggs=('', str, ''))
    assert c.foo == True
    assert c.bar == 4
    assert c.eggs == 'bla bla bla'

    # Config with string, implicit section, different name
    c = Config('aaaa', SAMPLE1,
               foo=(False, bool, ''), bar=(1, int, ''),
               spam=(0.0, float, ''), eggs=('', str, ''))
    assert c.foo == True
    assert c.bar == 3

    # Config with string, explicit section, different name (no section match)
    c = Config('aaaa', SAMPLE2,
               foo=(False, bool, ''), bar=(1, int, ''),
               spam=(0.0, float, ''), eggs=('', str, ''))
    assert c.foo == False
    assert c.bar == 1

    # Config with both, and filenames can be nonexistent
    c = Config('testconfig', SAMPLE1, filename2, filename1+'.cfg',
               foo=(False, bool, ''), bar=(1, int, ''),
               spam=(0.0, float, ''), eggs=('', str, ''))
    assert c.bar == 4
    #
    c = Config('testconfig', filename2, filename1+'.cfg', SAMPLE1,
               foo=(False, bool, ''), bar=(1, int, ''),
               spam=(0.0, float, ''), eggs=('', str, ''))
    assert c.bar == 3

    # Config from invalid string is ignored (logged)
    c = Config('testconfig', SAMPLE3, bar=(1, int, ''))
    assert c.bar == 1

    # Config from invalid file is ignored (logged)
    c = Config('testconfig', filename3, bar=(1, int, ''))
    assert c.bar == 1

    # Config from invalid unidocde file is ignored (logged)
    c = Config('testconfig', filename4, bar=(1, int, ''))
    assert c.bar == 1

    # Fails
    with raises(ValueError):
        c = Config('testconfig', [])
    with raises(ValueError):
        c = Config('testconfig', 3)


def test_read_file_later():

    filename1 = os.path.join(tempfile.gettempdir(), 'flexx_config_test1.cfg')
    with open(filename1, 'wb') as f:
        f.write(SAMPLE1.encode())
    filename2 = os.path.join(tempfile.gettempdir(), 'flexx_config_test2.cfg')
    with open(filename2, 'wb') as f:
        f.write(SAMPLE2.encode())

    os.environ['TESTCONFIG_SPAM'] = '100'
    c = Config('testconfig', filename1,
               foo=(False, bool, ''), bar=(1, int, ''),
               spam=(0.0, float, ''), eggs=('', str, ''))
    del os.environ['TESTCONFIG_SPAM']

    assert c.bar == 3  # from filename1
    assert c.spam == 100
    c.eggs = 'haha'
    c.spam = 10

    c.load_from_file(filename2)
    assert c.bar == 4  # from filename2
    assert c.eggs == 'haha'  # from what we set - takes precedense
    assert c.spam == 10  # from what we set - precedense over env var


def test_access():

    c = Config('testconfig', foo=(1, int, ''), BAR=(1, int, ''))
    assert len(c) == 2

    c.foo = 3
    c.BAR = 4
    assert c['foo'] == 3
    assert c['BAR'] == 4
    c['foO'] = 30
    c['BAr'] = 40
    assert c['FOO'] == 30
    assert c['bar'] == 40

    with raises(AttributeError):
        c.FOO
    with raises(AttributeError):
        c.bar
    with raises(TypeError):
        c[3]
    with raises(IndexError):
        c['optiondoesnotexist']
    with raises(TypeError):
        c[3] = ''
    with raises(IndexError):
        c['optiondoesnotexist'] = ''


def test_repr_and_str():

    # Prepare file
    filename1 = os.path.join(tempfile.gettempdir(), 'flexx_config_test1.cfg')
    with open(filename1, 'wb') as f:
        f.write(SAMPLE1.encode())

    c = Config('aaa', foo=(False, bool, ''), bar=(1, int, ''))

    r = repr(c)
    summary = str(c)
    summary1 = summary.splitlines()[0]

    # Test repr
    assert 'aaa' in r
    assert r.startswith('<') and r.endswith('>')
    assert '2' in r  # shows how many options

    # Test first line of summary
    assert 'aaa' in summary1
    assert '2' in summary1
    assert 'default' in summary
    assert not 'set' in summary
    assert not 'string' in summary

    # set some
    c.bar = 2
    summary = str(c)
    summary1 = summary.splitlines()[0]

    # Continue
    assert 'default' in summary
    assert 'set' in summary

    assert summary.count('default') == 2  # once for each opt
    assert summary.count('set') == 1  # once for one opt

    # Again, now with a file
    c = Config('aaa', filename1, foo=(False, bool, ''), bar=(1, int, ''))
    summary = str(c)
    summary1 = summary.splitlines()[0]

    # Test first line of summary
    assert 'aaa' in summary1
    assert '2' in summary1
    assert 'default' in summary
    assert filename1 in summary
    assert not 'set' in summary
    assert not 'string' in summary

    # Again, now with a string
    c = Config('aaa', SAMPLE1, foo=(False, bool, ''), bar=(1, int, ''))
    summary = str(c)
    summary1 = summary.splitlines()[0]

    # Test first line of summary
    assert 'aaa' in summary1
    assert '2' in summary1
    assert 'default' in summary
    assert filename1 not in summary
    assert not 'set' in summary
    assert 'string' in summary


def test_set_from_cmdline():

    old_argv = sys.argv

    try:

        sys.argv = '', '--aaa-bar=9'
        c = Config('aaa', SAMPLE1, foo=(False, bool, ''), bar=(1, int, ''))
        assert c.bar == 9

        sys.argv = '', '--aAa-bAr=9'
        c = Config('aaa', SAMPLE1, foo=(False, bool, ''), bar=(1, int, ''))
        assert c.bar == 9  # case insensitive

        sys.argv = '', '--aaa-bar', '9'
        c = Config('aaa', SAMPLE1, foo=(False, bool, ''), bar=(1, int, ''))
        assert c.bar == 3  # need syntax using equals sign

        sys.argv = '', '--bar', '9'
        c = Config('aaa', SAMPLE1, foo=(False, bool, ''), bar=(1, int, ''))
        assert c.bar == 3  # neeed name prefix

        sys.argv = '', '--aaa-foo=1,2,3'
        c = Config('aaa', foo=([], [int], ''))
        assert c.foo == (1, 2, 3)

    finally:
        sys.argv = old_argv


def test_set_from_env():

    name = 'config_env_test'

    os.environ[name.upper() + '_' + 'BAR'] = '8'
    c = Config(name, SAMPLE1, foo=(False, bool, ''), bar=(1, int, ''))
    del os.environ[name.upper() + '_' + 'BAR']
    assert c.bar == 8

    os.environ[name + '-' + 'bar'] = '8'
    c = Config(name, SAMPLE1, foo=(False, bool, ''), bar=(1, int, ''))
    del os.environ[name + '-' + 'bar']
    assert c.bar == 3  # must be uppercase

    os.environ[name.upper() + '-' + 'bar'] = '8'
    c = Config(name, SAMPLE1, foo=(False, bool, ''), bar=(1, int, ''))
    del os.environ[name.upper() + '-' + 'bar']
    assert c.bar == 3  # should use underscore


def test_order():

    filename1 = os.path.join(tempfile.gettempdir(), 'flexx_config_test1.cfg')
    with open(filename1, 'wb') as f:
        f.write(SAMPLE1.encode())
    filename2 = os.path.join(tempfile.gettempdir(), 'flexx_config_test2.cfg')
    with open(filename2, 'wb') as f:
        f.write(SAMPLE2.encode())

    old_argv = sys.argv
    os.environ['TESTCONFIG_BAR'] = '5'
    sys.argv = '', '--testconfig-bar=6'

    try:
        c = Config('testconfig', filename1, filename2,
                   bar=(2, int, ''))
    finally:
        del os.environ['TESTCONFIG_BAR']
        sys.argv = old_argv

    c.bar = 7

    s = str(c)
    indices1 = [s.index(' %i '%i) for i in [2, 3, 4, 5, 6, 7]]
    indices2 = [s.rindex(' %i '%i) for i in [2, 3, 4, 5, 6, 7]]
    indices3 = list(sorted(indices1))
    assert indices1 == indices3
    assert indices2 == indices3


def test_docstring():

    c = Config('aaa', foo=(False, bool, ''), bar=(1, int, ''))

    assert 'aaa' in c.__doc__
    assert 'foo (bool)' in c.__doc__
    assert 'bar (int)' in c.__doc__


def test_bool():
    c = Config('testconfig', foo=(True, bool, ''), bar=(False, bool, ''))
    assert c.foo == True
    c.foo = True
    assert c.foo == True
    c.foo = False
    assert c.foo == False

    for name in 'yes on true Yes On TRUE 1'.split(' '):
        c.foo = name
        assert c.foo == True
    for name in 'no off fAlse No Off FALSE 0'.split(' '):
        c.foo = name
        assert c.foo == False

    for name in 'none ok bla asdasdasd cancel'.split(' '):
        with raises(ValueError):
            c.foo = name

    for val in (1, 2, [2], None, 0, 0.0, 1.0, []):
        with raises(ValueError):
            c.foo = val


def test_int():
    c = Config('testconfig', foo=(1, int, ''), bar=('1', int, ''))
    assert c.foo == 1
    assert c.bar == 1

    c.foo = 12.1
    assert c.foo == 12
    c.foo = '7'
    assert c.foo == 7
    c.foo = '-23'
    assert c.foo == -23

    for val in ([], None, '1e2', '12.1', 'a'):
        with raises(ValueError):
            c.foo = val


def test_float():
    c = Config('testconfig', foo=(1, float, ''), bar=('1', float, ''))
    assert c.foo == 1.0
    assert c.bar == 1.0

    c.foo = 3
    assert c.foo == 3.0
    c.foo = -3.1
    assert c.foo == -3.1
    c.foo = '2e3'
    assert c.foo == 2000.0
    c.foo = '12.12'
    assert c.foo == 12.12

    for val in ([], None, 'a', '0a'):
        with raises(ValueError):
            c.foo = val


def test_str():
    c = Config('testconfig', foo=(1, str, ''), bar=((1,2,3), str, ''))
    assert c.foo == '1'
    assert c.bar == '(1, 2, 3)'

    c.foo = 3
    assert c.foo == '3'
    c.foo = 3.1
    assert c.foo == '3.1'
    c.foo = 'hello there, you!'
    assert c.foo == 'hello there, you!'
    c.foo = None
    assert c.foo == 'None'
    c.foo = False
    assert c.foo == 'False'
    c.foo = []
    assert c.foo == '[]'


def test_tuple():
    c = Config('testconfig', foo=('1,2', [int], ''), bar=((1,2,3), [str], ''))
    assert c.foo == (1, 2)
    assert c.bar == ('1', '2', '3')

    c.foo = 1.2, 3.3, 5
    assert c.foo == (1, 3, 5)
    c.foo = '(7, 8, 9)'
    assert c.foo == (7, 8, 9)
    c.foo = '1,               2,-3,4'
    assert c.foo == (1, 2, -3, 4)
    c.foo = [1, '2']
    assert c.foo == (1, 2)


    for val in ([[]], [None], ['a'], ['0a'], ['1.2'], 3):
        with raises(ValueError):
            c.foo = val

    c.bar = 'hello,  there,     you '
    assert c.bar == ('hello', 'there', 'you')
    c.bar = [1, '2']
    assert c.bar == ('1', '2')


run_tests_if_main()
