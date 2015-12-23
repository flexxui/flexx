""" This tests the Model class.
"""

from flexx.util.testing import run_tests_if_main, raises

from flexx.app.model import Model, JSSignal, PySignal
from flexx import react


class Foo1(Model):
    
    @react.input
    def title(v=''):
        return v
    
    class JS:
        
        @react.input
        def blue(v=0):
            return v


class Foo2(Foo1):
    
    @react.connect('title')
    def title_len(v):
        return len(v)
    
    class JS:
        
        @react.connect('blue')
        def red(v):
            return v + 1


class Foo3(Foo2):
    py_attr = 42
    
    @react.input
    def js_attr(v=0):
        return v
    
    class JS:
        js_attr = 42
        
        @react.input
        def py_attr(v=0):
            return v


class Foo4(Foo3):
    
    @react.input
    def title(v='a'):
        return v
    
    class JS:
        
        @react.connect('blue')
        def red(v):
            return v + 2



def test_signal_pairing1():
    
    assert isinstance(Foo2.title, react.Signal)
    assert isinstance(Foo2.blue, react.Signal)
    
    assert isinstance(Foo2.JS.title, react.Signal)
    assert isinstance(Foo2.JS.blue, react.Signal)
    
    assert not isinstance(Foo2.title, JSSignal)
    assert isinstance(Foo2.blue, JSSignal)
    
    assert isinstance(Foo2.JS.title, PySignal)
    assert not isinstance(Foo2.JS.blue, PySignal)


def test_signal_pairing2():
    
    assert isinstance(Foo2.title, react.Signal)
    assert isinstance(Foo2.title_len, react.Signal)
    assert isinstance(Foo2.blue, react.Signal)
    assert isinstance(Foo2.red, react.Signal)
    
    assert isinstance(Foo2.JS.title, react.Signal)
    assert isinstance(Foo2.JS.title_len, react.Signal)
    assert isinstance(Foo2.JS.blue, react.Signal)
    assert isinstance(Foo2.JS.red, react.Signal)
    
    assert not isinstance(Foo2.title, JSSignal)
    assert not isinstance(Foo2.title_len, JSSignal)
    assert isinstance(Foo2.blue, JSSignal)
    assert isinstance(Foo2.red, JSSignal)
    
    assert isinstance(Foo2.JS.title, PySignal)
    assert isinstance(Foo2.JS.title_len, PySignal)
    assert not isinstance(Foo2.JS.blue, PySignal)
    assert not isinstance(Foo2.JS.red, PySignal)


def test_signal_pairing4():
    # This is basically a double-check on test_signal_pairing2
    assert isinstance(Foo4.title, react.Signal)
    assert isinstance(Foo4.title_len, react.Signal)
    assert isinstance(Foo4.blue, react.Signal)
    assert isinstance(Foo4.red, react.Signal)
    
    assert isinstance(Foo4.JS.title, react.Signal)
    assert isinstance(Foo4.JS.title_len, react.Signal)
    assert isinstance(Foo4.JS.blue, react.Signal)
    assert isinstance(Foo4.JS.red, react.Signal)
    
    assert not isinstance(Foo4.title, JSSignal)
    assert not isinstance(Foo4.title_len, JSSignal)
    assert isinstance(Foo4.blue, JSSignal)
    assert isinstance(Foo4.red, JSSignal)
    
    assert isinstance(Foo4.JS.title, PySignal)
    assert isinstance(Foo4.JS.title_len, PySignal)
    assert not isinstance(Foo4.JS.blue, PySignal)
    assert not isinstance(Foo4.JS.red, PySignal)


def test_signal_no_clashes():
    
    # Attributes that already exist are not overwritten
    assert Foo3.py_attr == 42
    assert Foo3.JS.js_attr == 42
    
    assert isinstance(Foo3.js_attr, react.Signal)
    assert isinstance(Foo3.JS.py_attr, react.Signal)
    
    # Double check in subclass
    assert Foo4.py_attr == 42
    assert Foo4.JS.js_attr == 42
    
    assert isinstance(Foo4.js_attr, react.Signal)
    assert isinstance(Foo4.JS.py_attr, react.Signal)


def test_overloading():
    
    assert Foo2.title is Foo1.title
    assert Foo3.JS.red is Foo2.JS.red
    
    assert Foo4.title is not Foo1.title
    assert Foo4.JS.red is not Foo2.JS.red


def test_no_duplicate_code():
    assert '_blue_func' in Foo1.JS.CODE
    assert '_blue_func' not in Foo2.JS.CODE
    assert '_blue_func' not in Foo4.JS.CODE
    
    assert '_red_func' not in Foo1.JS.CODE
    assert '_red_func' in Foo2.JS.CODE
    assert '_red_func' in Foo4.JS.CODE


run_tests_if_main()
