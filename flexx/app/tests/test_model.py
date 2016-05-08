""" This tests the Model class.
"""

from flexx.util.testing import run_tests_if_main, raises

from flexx.app.model import Model
from flexx import event


class Foo1(Model):
    
    @event.prop
    def title(self, v=''):
        return v
    
    class JS:
        
        @event.prop
        def blue(self, v=0):
            return v

class Foo2(Foo1):
    
    class JS:
        
        @event.prop
        def red(self, v=0):
            return v


class Foo3(Foo2):
    py_attr = 42
    
    @event.prop
    def js_attr(self, v=0):
        return v
    
    class JS:
        js_attr = 42
        
        @event.prop
        def py_attr(self, v=0):
            return v

class Foo4(Foo3):
    
    @event.prop
    def title(self, v=''):
        return v + 'x'
    
    class JS:
        
        @event.prop
        def red(self, v=0):
            return v+1


def test_pairing1():
    
    assert isinstance(Foo1.title, event._emitters.Property)
    assert isinstance(Foo1.blue, event._emitters.Property)
    
    assert isinstance(Foo1.JS.title, event._emitters.Property)
    assert isinstance(Foo1.JS.blue, event._emitters.Property)


def test_no_clashes():
    
    # Attributes that already exist are not overwritten
    assert Foo3.py_attr == 42
    assert Foo3.JS.js_attr == 42
    
    assert isinstance(Foo3.js_attr, event._emitters.Property)
    assert isinstance(Foo3.JS.py_attr, event._emitters.Property)
    
    # Double check in subclass
    assert Foo4.py_attr == 42
    assert Foo4.JS.js_attr == 42
    
    assert isinstance(Foo4.js_attr, event._emitters.Property)
    assert isinstance(Foo4.JS.py_attr, event._emitters.Property)


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
