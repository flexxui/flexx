""" Tests for the bare handlers.

Does not test dynamism currently, as we will test that extensively in
test_both.
"""

import gc
import sys
import weakref

from flexx.util.testing import run_tests_if_main, skipif, skip, raises

from flexx import event


def test_method_handlers():
    
    events1 = []
    events2 = []
    class Foo(event.HasEvents):
        
        @event.connect('x1')
        def handle1(self, *events):
            events1.extend(events)
        
        @event.connect('x1', 'x2')
        def handle2(self, *events):
            events2.extend(events)
    
    foo = Foo()
    with event.loop:
        foo.emit('x1', {})
        foo.emit('x2', {})
    
    assert len(events1) == 1
    assert len(events2) == 2
    
    assert isinstance(foo.handle1, event._handler.Handler)
    assert repr(foo.handle1)
    assert hasattr(foo.handle1, 'dispose')
    assert foo.handle1.get_name() == 'handle1'
    assert foo.handle1.get_connection_info() == [('x1', ['x1', ])]
    assert foo.handle2.get_connection_info() == [('x1', ['x1', ]), ('x2', ['x2', ])]
    
    # Can't touch this
    with raises(AttributeError):
        foo.handle1 = 3
    with raises(AttributeError):
        del foo.handle1


def test_method_handlers_nodecorator():
    
    events1 = []
    events2 = []
    class Foo(event.HasEvents):
        
        def _handle1(self, *events):
            events1.extend(events)
        handle1 = event.connect(_handle1, 'x1')
        
        def _handle2(self, *events):
            events2.extend(events)
        handle2 = event.connect(_handle2, 'x1', 'x2')
    
    foo = Foo()
    with event.loop:
        foo.emit('x1', {})
        foo.emit('x2', {})
    
    assert len(events1) == 1
    assert len(events2) == 2
    
    assert isinstance(foo.handle1, event._handler.Handler)
    assert repr(foo.handle1)
    assert hasattr(foo.handle1, 'dispose')
    assert foo.handle1.get_name() == '_handle1'  # note the name ...
    
    # Can't touch this
    with raises(AttributeError):
        foo.handle1 = 3
    with raises(AttributeError):
        del foo.handle1


def test_func_handlers():
    
    events1 = []
    events2 = []
    class Foo(event.HasEvents):
        pass
    
    foo = Foo()
    
    @foo.connect('x1')
    def handle1(*events):
        events1.extend(events)
    
    @foo.connect('x1', 'x2')
    def handle2(*events):
        events2.extend(events)
    
    with event.loop:
        foo.emit('x1', {})
        foo.emit('x2', {})
    
    assert len(events1) == 1
    assert len(events2) == 2
    
    assert isinstance(handle1, event._handler.Handler)
    assert repr(handle1)
    assert hasattr(handle1, 'dispose')
    assert handle1.get_name() == 'handle1'
    assert handle1.get_connection_info() == [('x1', ['x1', ])]
    assert handle2.get_connection_info() == [('x1', ['x1', ]), ('x2', ['x2', ])]


def test_func_handlers_nodecorator():
    
    events1 = []
    events2 = []
    class Foo(event.HasEvents):
        pass
    
    foo = Foo()
    
    def _handle1(*events):
        events1.extend(events)
    handle1 = foo.connect(_handle1, 'x1')
    
    def _handle2(*events):
        events2.extend(events)
    handle2 = foo.connect(_handle2, 'x1', 'x2')
    
    with event.loop:
        foo.emit('x1', {})
        foo.emit('x2', {})
    
    assert len(events1) == 1
    assert len(events2) == 2
    
    assert isinstance(handle1, event._handler.Handler)
    assert repr(handle1)
    assert hasattr(handle1, 'dispose')
    assert handle1.get_name() == '_handle1'  # note the name


def test_func_handlers_nodecorator_reverse_connect_order():
    
    events1 = []
    events2 = []
    class Foo(event.HasEvents):
        pass
    
    foo = Foo()
    
    def _handle1(*events):
        events1.extend(events)
    handle1 = foo.connect('x1', _handle1)
    
    def _handle2(*events):
        events2.extend(events)
    handle2 = foo.connect('x1', 'x2', _handle2)
    
    with event.loop:
        foo.emit('x1', {})
        foo.emit('x2', {})
    
    assert len(events1) == 1
    assert len(events2) == 2
    
    assert isinstance(handle1, event._handler.Handler)
    assert repr(handle1)
    assert hasattr(handle1, 'dispose')
    assert handle1.get_name() == '_handle1'  # note the name


def test_func_handlers_with_method_decorator():

    with raises(TypeError):  # error because needs self as first arg
        @event.connect('x')
        def foo(*events):
            pass
    
    # We can fool Flexx by putting self as a first arg. No way for Flexx to see
    # that this is not a method.
    @event.connect('x')
    def foo(self, *events):
        pass
    
    assert isinstance(foo, event._handler.HandlerDescriptor)
    assert repr(foo)


def test_handler_builtin_function():
    
    class Foo(event.HasEvents):
        pass
    
    foo = Foo()
    foo.connect('!bar', print)  # this should not error


def test_method_handler_invoking():
    called = []
    
    class MyObject(event.HasEvents):
        
        @event.connect('x1', 'x2')
        def handler(self, *events):
            print(events)
            called.append(len(events))
        
        @event.connect('x3')
        def handler3(self, *events):
            called.append(len(events))
    
    h = MyObject()
    handler = h.handler
    
    handler()
    handler.handle_now()
    
    h.emit('x1', {})
    handler.handle_now()
    
    h.emit('x1', {})
    h.emit('x1', {})
    handler.handle_now()
    
    h.emit('x1', {})
    h.emit('x2', {})
    handler.handle_now()
    
    handler()
    handler.handle_now()
    
    h.handler3()
    handler.handle_now()
    
    assert called == [0, 1, 2, 2, 0, 0]


def test_func_handler_invoking():
    called = []
    
    h = event.HasEvents()
    
    @h.connect('x1', 'x2')
    def handler(*events):
        called.append(len(events))
    
    handler()
    handler.handle_now()
    
    h.emit('x1', {})
    handler.handle_now()
    
    h.emit('x1', {})
    h.emit('x1', {})
    handler.handle_now()
    
    h.emit('x1', {})
    h.emit('x2', {})
    handler.handle_now()
    
    handler()
    handler.handle_now()
    
    assert called == [0, 1, 2, 2, 0]


def test_method_handler_invoking_other():
    
    h = event.HasEvents()
    
    # This used not not work
    # with raises(RuntimeError):
    #     class Foo(event.HasEvents):
    #         
    #         @h.connect('x1')
    #         def handler(self, *events):
    #             self.was_invoked = True
    
    # But now it does!
    
    class Foo(event.HasEvents):
        
        @h.connect('x1')
        def handler(self, *events):
            self.was_invoked = True
    
    foo = Foo()
    
    h.emit('x1')
    event.loop.iter()
    assert foo.was_invoked


def test_connecting():
    
    # We've done all the normal connections. We test mosly fails here
    
    h = event.HasEvents()
    
    with raises(RuntimeError):  # connect() needs args
        @event.connect
        def foo(*events):
            pass
    with raises(RuntimeError):
        @h.connect
        def foo(*events):
            pass
    
    with raises(ValueError):  # connect() needs strings
        @event.connect(3)
        def foo(*events):
            pass
    with raises(ValueError):
        @h.connect(3)
        def foo(*events):
            pass
    
    with raises(TypeError):  # connect() needs callable
        event.connect('x')(3)
    with raises(TypeError):  # connect() needs callable
        h.connect('x')(3)
    
    with raises(RuntimeError):  # cannot connect
        h.xx = None
        @h.connect('xx.foobar')
        def foo(*events):
            pass

def test_connecting_and_getting_cached_event():
    
    h = event.HasEvents()
    h.emit('foo')
    
    res = []
    @h.connect('foo')
    def handle(ev):
        res.append(ev)
    
    event.loop.iter()
    event.loop.iter()
    assert len(res) == 1


def test_exceptions1():
    h = event.HasEvents()
    
    @h.connect('foo')
    def handle_foo(*events):
        1/0
    
    h.emit('foo', {})
    
    sys.last_traceback = None
    assert sys.last_traceback is None
    
    # No exception should be thrown here
    event.loop.iter()
    event.loop.iter()
    
    # But we should have prepared for PM debugging
    if sys.version_info[0] >= 3:  # not sure why
        assert sys.last_traceback
    
    # Its different for a direct call
    with raises(ZeroDivisionError):
        handle_foo()


def test_exceptions2():
    
    class Foo(event.HasEvents):
        def __init__(self):
            super().__init__()
            self.bar = event.HasEvents()
            self.bars = [self.bar]
    
    f = Foo()
    
    # ok
    @f.connect('bars.*.spam')
    def handle_foo(*events):
        pass
    
    # not ok
    with raises(RuntimeError) as err:
        @f.connect('bar.*.spam')
        def handle_foo(*events):
            pass
    assert 'not a tuple' in str(err)


def test_dispose1():
    
    h = event.HasEvents()
    
    @h.connect('x1', 'x2')
    def handler(*events):
        pass
    
    handler_ref = weakref.ref(handler)
    del handler
    gc.collect()
    assert handler_ref() is not None  # h is holding on
    
    handler_ref().dispose()
    gc.collect()
    assert handler_ref() is None


def test_dispose2():
    
    h = event.HasEvents()
    
    @h.connect('x1', 'x2')
    def handler(*events):
        pass
    
    handler_ref = weakref.ref(handler)
    del handler
    gc.collect()
    assert handler_ref() is not None  # h is holding on
    
    h.dispose()  # <=== only this line is different from test_dispose1()
    gc.collect()
    assert handler_ref() is None


def test_dispose3():
    # Test that connecting a "volatile" object to a static object works well
    # w.r.t. cleanup.
    
    relay = event.HasEvents()
    
    class Foo:
        def bar(self, *events):
            pass
    
    foo = Foo()
    handler = relay.connect(foo.bar, 'xx')
    
    handler_ref = weakref.ref(handler)
    foo_ref = weakref.ref(foo)
    
    del foo
    del handler
    
    gc.collect()
    
    assert foo_ref() is None
    assert handler_ref() is not None
    
    relay.emit('xx')
    event.loop.iter()
    gc.collect()
    
    assert foo_ref() is None
    assert handler_ref() is None


run_tests_if_main()
