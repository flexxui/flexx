""" Basic tests for emitters. Does not contain an awefull extensive
test suite, as we test emitters quite well in test_both.py.
"""

from flexx.util.testing import run_tests_if_main, skipif, skip, raises

from flexx import event


def test_property():
    
    class MyObject(event.HasEvents):
        
        @event.prop
        def foo(self, v=1.2):
            return float(v)
        
        @event.prop
        def bar(self, v=1.3):
            return float(v)
    
    m = MyObject()
    assert m.foo == 1.2
    assert m.bar == 1.3
    
    m = MyObject(foo=3)
    assert m.foo == 3.0
    
    m.foo = 5.1
    m.bar = 5.1
    assert m.foo == 5.1
    assert m.bar == 5.1
    
    m.foo = '9.3'
    assert m.foo == 9.3
    
    m = MyObject(foo=3)
    assert m.foo == 3.0
    
    # Hacky, but works
    def foo():
        pass
    x = event.prop(foo)
    assert 'foo' in repr(x)
    
    spam = lambda x:None
    x = event.prop(spam)
    assert '<lambda>' in repr(x)
    
    # fails
    
    with raises(ValueError):
        m.foo = 'bla'
    
    with raises(ValueError):
        MyObject(foo='bla')
    
    with raises(TypeError):
        m._set_prop(3, 3)  # Property name must be a string
        
    with raises(AttributeError):
        m._set_prop('spam', 3)  # MyObject has not spam property
    
    with raises(AttributeError):
        MyObject(spam='bla')  # MyObject has not spam property
    
    with raises(TypeError):
        event.prop(3)  # prop decorator needs callable
    
    with raises(AttributeError):
        del m.foo  # cannot delete a property
    
    class MyObject2(event.HasEvents):
        
        @event.prop
        def foo(self, v):
            return float(v)
    
    #with raises(RuntimeError):
    #    MyObject2()  # no default value for foo
    ob = MyObject2()
    assert ob.foo is None


def test_prop_recursion():
    class MyObject(event.HasEvents):
        count = 0
        
        @event.prop
        def foo(self, v=1):
            v = float(v)
            self.bar = v + 1
            return v
        
        @event.prop
        def bar(self, v=2):
            v = float(v)
            self.foo = v - 1
            return v
        
        @event.connect('foo', 'bar')
        def handle(self, *events):
            self.count += 1
    
    m = MyObject()
    event.loop.iter()
    assert m.count == 1
    assert m.foo == 1
    assert m.bar== 2
    
    m = MyObject(foo=3)
    event.loop.iter()
    assert m.count == 1
    assert m.foo == 3
    assert m.bar== 4
    
    m.foo = 50
    event.loop.iter()
    assert m.count == 2
    assert m.foo == 50
    assert m.bar== 51
    
    m.bar = 50
    event.loop.iter()
    assert m.count == 3
    assert m.foo == 49
    assert m.bar== 50


def test_prop_init():
    class MyObject(event.HasEvents):
        
        @event.prop
        def foo(self, v=1):
            return float(v)
        
        @event.connect('foo')
        def foo_handler(self, *events):
            pass
    
    m = MyObject()
    assert len(m.foo_handler._pending) == 1
    m.foo = 2
    m.foo = 3
    assert len(m.foo_handler._pending) == 3
    m.foo = 3
    assert len(m.foo_handler._pending) == 3
    
    # Specifying the value in the init will result in just one event
    m = MyObject(foo=9)
    assert len(m.foo_handler._pending) == 2
    m.foo = 2
    m.foo = 3
    assert len(m.foo_handler._pending) == 4
    m.foo = 3
    assert len(m.foo_handler._pending) == 4
    

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
    
    with raises(TypeError):
        event.readonly(3)  # readonly decorator needs callable
    
    with raises(AttributeError):
        del m.foo  # cannot delete a readonly
        
    class MyObject2(event.HasEvents):
        
        @event.readonly
        def foo(self, v):
            return float(v)
    
    #with raises(RuntimeError):
    #    MyObject2()  # no default value for foo
    ob = MyObject2()
    assert ob.foo is None


def test_emitter():
    
    class MyObject(event.HasEvents):
        
        @event.emitter
        def foo(self, v):
            return dict(value=float(v))
        
        @event.emitter
        def bar(self, v):
            return dict(value=float(v)+1)  # note plus 1
        
        @event.connect('foo')
        def on_foo(self, *events):
            self.the_val = events[0].value  # so we can test it
        
        @event.connect('bar')
        def on_bar(self, *events):
            self.the_val = events[0].value  # so we can test it
    
    m = MyObject()
    
    the_vals = []
    @m.connect('foo', 'bar')
    def handle_foo(*events):
        the_vals.append(events[0].value)
    
    with event.loop:
        m.foo(3.2)
    assert m.the_val == 3.2
    assert the_vals[-1] == 3.2
    
    with event.loop:
        m.foo('9.1')
    assert m.the_val == 9.1
    assert the_vals[-1] == 9.1
    
    with event.loop:
        m.bar(3.2)
    assert m.the_val == 4.2
    assert the_vals[-1] == 4.2
    
    # Fail
    
    with raises(ValueError):
        m.foo('bla')
    
    with raises(TypeError):
        event.emitter(3)  # emitter decorator needs callable
    
    with raises(AttributeError):
        del m.foo  # cannot delete an emitter
    
    with raises(AttributeError):
        m.foo = None  # cannot set an emitter
    
    class MyObject2(event.HasEvents):
        
        @event.emitter
        def foo(self, v):
            return float(v)
    
    with raises(TypeError):
        m = MyObject2()
        m.foo(3.2)  # return value of emitter must be a dict


run_tests_if_main()
