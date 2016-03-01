""" Basic tests for emitters. Does not contain an awefull extensive
test suite, as we test emitters quite well in test_both.py.
"""

from flexx.util.testing import run_tests_if_main, skipif, skip, raises

from flexx import event


# todo: test that we get an event for default value and also for initial value passed in init. Or not?

def test_property():
    
    class MyObject(event.HasEvents):
        
        @event.prop
        def foo(self, v=1.2):
            return float(v)
    
    m = MyObject()
    assert m.foo == 1.2
    
    m = MyObject(foo=3)
    assert m.foo == 3.0
    
    m.foo = 5.1
    assert m.foo == 5.1
    
    m.foo = '9.3'
    assert m.foo == 9.3
    
    # fails
    
    with raises(ValueError):
        m.foo = 'bla'
    
    with raises(ValueError):
        MyObject(foo='bla')
    
    
    class MyObject2(event.HasEvents):
        
        @event.prop
        def foo(self, v):
            return float(v)
    
    with raises(RuntimeError):
        MyObject2()  # no default value for foo


def test_readonly():
    class MyObject(event.HasEvents):
        
        @event.readonly
        def foo(self, v=1.2):
            return float(v)
    
    m = MyObject()
    assert m.foo == 1.2
    
    
    m._set_prop('foo', 5.1)
    assert m.foo == 5.1
    
    m._set_prop('foo', '9.3')
    assert m.foo == 9.3
    
    # fails
    
    with raises(AttributeError):
        m.foo = 3.1
    
    with raises(AttributeError):
        m.foo = 'bla'
    
    with raises(AttributeError):
        MyObject(foo=3.2)
    
    
    class MyObject2(event.HasEvents):
        
        @event.readonly
        def foo(self, v):
            return float(v)
    
    with raises(RuntimeError):
        MyObject2()  # no default value for foo


def test_emitter():
    
    class MyObject(event.HasEvents):
        
        @event.emitter
        def foo(self, v):
            return dict(value=float(v))
        
        def on_foo(self, *events):
            self.the_val = events[0].value  # so we can test it
    
    m = MyObject()
    
    with event.loop:
        m.foo(3.2)
    assert m.the_val == 3.2
    
    with event.loop:
        m.foo('9.1')
    assert m.the_val == 9.1
    
    # Fail
    
    with raises(ValueError):
        m.foo('bla')
    
    
    class MyObject2(event.HasEvents):
        
        @event.emitter
        def foo(self, v):
            return float(v)
    
    with raises(TypeError):
        m = MyObject2()
        m.foo(3.2)  # return value of emitter must be a dict


run_tests_if_main()
