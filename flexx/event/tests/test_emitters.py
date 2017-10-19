""" Basic tests for emitters. Does not contain an awefull extensive
test suite, as we test emitters quite well in test_both.py.
"""


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
