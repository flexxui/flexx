"""
Tests that should run in both Python and JS.
This helps ensure that both implementation work in the same way.

Focus on use-cases rather than coverage.

These tests work a bit awkward, but its very useful to be able to test
that the two systems work exactly the same way. You define a class with
signals, and then provide that class to a test function using a
decorator. The test function will then be run both in Python and in JS.
The test function should return an object, that when evaluates to a
string matches with the reference string given to the decorator. The
result string is made lowercase, and double quotes are converted to
single quotes.

"""

from pytest import raises
from flexx.util.testing import run_tests_if_main

from flexx.reactive import input, signal, react, source, HasSignals
from flexx.reactive.pyscript import create_js_signals_class, HasSignalsJS
from flexx.pyscript import js, evaljs, evalpy


def run_in_both(cls, reference):
    
    if reference.lower() != reference:
        raise ValueError('Test reference should be lowercase!')
    
    def wrapper(func):
        def runner():
            # Run in JS
            code = HasSignalsJS.jscode
            code += create_js_signals_class(cls, cls.__name__)
            code += 'var test = ' + js(func).jscode
            code += 'test(%s);' % cls.__name__
            jsresult = evaljs(code)
            jsresult = jsresult.replace('[ ', '[').replace(' ]', ']')
            jsresult = jsresult.replace('"', "'")
            print('js:', jsresult)
            # Run in Python
            pyresult = str(func(cls))
            pyresult = pyresult.replace('"', "'")
            print('py:', pyresult)
            #
            assert pyresult.lower() == reference
            assert jsresult.lower() == reference
        return runner
    return wrapper


class Name(HasSignals):
    
    def __init__(self):
        self.r = []
        super().__init__()
    
    @input
    def first_name(v='john'):
        return str(v)
    
    @input
    def last_name(v='doe'):
        return str(v)
    
    @signal('first_name', 'last_name')
    def full_name(self, n1, n2):
        self.r.append('')
        return n1 + ' ' + n2

@run_in_both(Name, "['', 'john doe', '', 'almar klein', '', 'jorik klein']")
def test_pull(Name):
    name = Name()
    name.r.append(name.full_name())
    name.first_name('almar')
    name.last_name('klein')
    name.r.append(name.full_name())
    name.first_name('jorik')
    name.r.append(name.full_name())
    return name.r

@run_in_both(Name, "[true, true, '', true, true, true, true, '', true, true]")
def test_attributes(Name):
    s = Name()
    s.r.append(s.full_name._timestamp == 0)
    s.r.append(s.full_name._value is None)
    s.full_name()
    s.r.append(s.full_name._timestamp > 0)
    s.r.append(s.full_name._last_timestamp == 0)
    s.r.append(s.full_name._value == 'john doe')
    s.r.append(s.full_name._last_value is None)
    s.first_name('jane')
    s.full_name()
    s.r.append(s.full_name._last_timestamp > 0)
    s.r.append(s.full_name._last_value == 'john doe')
    return s.r


class Title(HasSignals):
    
    def __init__(self):
        self.r = []
        super().__init__()
    
    @input
    def title(v=''):
        return v
    
    @signal('title')
    def title_len(v):
        return len(v)
    
    @react('title_len')
    def show_title(self, v):
        self.r.append(v)

@run_in_both(Title, '[0, 2, 4, false]')
def test_push(Title):
    foo = Title()
    foo.title('xx')
    foo.title('xxxx')
    foo.r.append(foo.show_title.not_connected)
    return foo.r

@run_in_both(Title, "[0, 1, 2, 3]")
def test_disconnecting(Title):
    s = Title()
    
    s.show_title.disconnect()
    s.title('xx')
    s.title('xxxxx')
    s.title('x')
    s.show_title.connect()  # auto-connect
    assert not s.show_title.not_connected
    
    s.title_len.disconnect()
    s.title('xxx')
    s.title('xxxxx')
    s.title('xx')
    s.show_title()  # auto-connect does not work now
    assert s.title_len.not_connected
    
    s.title('xx')
    s.title('xxxxx')
    s.title('xxx')
    s.title_len.connect()  # connected again
    assert not s.title_len.not_connected
    
    return s.r
    

class Unconnected(HasSignals):
    
    @input
    def s1(v=''):
        return v
    
    @signal('nope')
    def s2(v):
        return v
    
    @signal('s2')
    def s3(v):
        return v

@run_in_both(Unconnected, "[false, 'signal 'nope' does not exist.']")
def test_unconnected(Cls):
    s = Cls()
    r = []
    r.append(s.s1.not_connected)
    r.append(s.s2.not_connected)
    return r

@run_in_both(Unconnected, "[true, false, 'err2', 'err3']")
def test_unconnected_handling(Cls):
    s = Cls()
    r = []
    r.append(bool(s.s2.not_connected))
    r.append(bool(s.s3.not_connected))
    #
    try:
        s.s2()
    except Exception:
        r.append('err2')
    try:
        s.s3()
    except Exception:
        r.append('err3')
    return r
    
test_unconnected_handling()
1/0

class SignalTypes(HasSignals):
    
    @input
    def s1(v):
        return v
    
    @source
    def s2(v):
        return v
    
    @signal('s2')
    def s3(v):
        return v
    
    @react('s2')
    def s4(v):
        return v

@run_in_both(SignalTypes, "['s2', 's3', 's4', 's3', 's4']")
def test_setting_inputs(Cls):
    s = Cls()
    r = []
    # These do not error
    s.s1('foo')
    s.s1._set('foo')
    s.s2._set('foo')
    # But these do
    try:
        s.s2('foo')
    except Exception:
        r.append('s2')
    try:
        s.s3('foo')
    except Exception:
        r.append('s3')
    try:
        s.s4('foo')
    except Exception:
        r.append('s4')
    # And these too
    try:
        s.s3._set('foo')
    except Exception:
        r.append('s3')
    try:
        s.s4._set('foo')
    except Exception:
        r.append('s4')
    return r

@run_in_both(SignalTypes, "[true, 'foo', 'bar']")
def test_setting_inputs2(Cls):
    s = Cls()
    r = []
    r.append(s.s1() is None)  # test no default value
    s.s1('foo')
    s.s2._set('bar')
    r.append(s.s1())
    r.append(s.s2())
    return r


class Circular(HasSignals):
    
    @input('s3')
    def s1(v1=10, v3=None):
        if v3 is None:
            return v1
        else:
            return v3 + 1
    
    @signal('s1')
    def s2(v):
        return v + 1
    
    @signal('s2')
    def s3(v):
        return v + 1

@run_in_both(Circular, "[10, 11, 12, '', 2, 3, 4]")
def test_circular(Cls):
    s = Cls()
    r = []
    r.append(s.s1())
    r.append(s.s2())
    r.append(s.s3())
    r.append('')
    s.s1(2)
    r.append(s.s1())
    r.append(s.s2())
    r.append(s.s3())
    return r


class Temperature(HasSignals):  # to avoid round erros, the relation is simplified
    @input('f')
    def c(v=32, f=None):
        if f is None:
            return int(v)
        else:
            return f - 32
    
    @input('c')
    def f(v=0, c=None):
        if c is None:
            return int(v)
        else:
            return c + 32

@run_in_both(Temperature, "[32, 0, '', 10, 42, '', -22, 10]")
def test_circular_temperature(Cls):
    s = Cls()
    r = []
    r.append(s.c())
    r.append(s.f())
    r.append('')
    s.c(10)
    r.append(s.c())
    r.append(s.f())
    r.append('')
    s.f(10)
    r.append(s.c())
    r.append(s.f())
    return r




run_tests_if_main()
