""" Tests for the bare HasEvents class.
"""

import gc
import sys
import weakref

from flexx.util.testing import run_tests_if_main, skipif, skip, raises

from flexx import event


def test_basics():
    
    # Simplest
    h = event.HasEvents()
    assert not h.__handlers__
    assert not h.__emitters__
    
    # Test __emitters__
    class Foo(event.HasEvents):
        @event.prop
        def a_prop(self, v=0):
            return v
        @event.readonly
        def a_readonly(self, v=0):
            return v
        @event.emitter
        def a_emitter(self, v):
            return {}
        @event.emitter  # deliberately define it twice
        def a_emitter(self, v):
            return {'x':1}
    #
    foo = Foo()
    assert not foo.__handlers__
    assert len(foo.__emitters__) == 1
    assert len(foo.__properties__) == 2
    assert 'a_prop' in foo.__properties__
    assert 'a_readonly' in foo.__properties__
    assert 'a_emitter' in foo.__emitters__
    #
    assert foo.get_event_types() == ['a_emitter', 'a_prop', 'a_readonly']
    assert foo.get_event_handlers('a_prop') == []
    
    # Test __handlers__
    class Bar(event.HasEvents):
        @event.connect('x')
        def spam(self, *events):
            pass
        @event.connect('eggs')
        def on_eggs(self, *events):
            pass
    #
    foo = Bar()
    assert not foo.__emitters__
    assert len(foo.__handlers__) == 2
    #assert len(foo.__handlers__) == 1
    assert 'spam' in foo.__handlers__
    assert 'on_eggs' in foo.__handlers__
    #
    assert foo.get_event_types() == ['eggs', 'x']
    assert foo.get_event_handlers('x') == [foo.spam]


def test_get_event_handlers():
    class Foo(event.HasEvents):
        @event.connect('x')
        def spam(self, *events):
            pass
        @event.connect('x')
        def eggs(self, *events):
            pass
    foo = Foo()
    @foo.connect('x')
    def bar(*events):
        pass
    
    # sorted by label name
    assert foo.get_event_handlers('x') == [bar, foo.eggs, foo.spam]
    
    @foo.connect('x')
    def zz1(*events):
        pass
    @foo.connect('x:a')
    def zz2(*events):
        pass
    
    # sorted by label name
    assert foo.get_event_handlers('x') == [zz2, bar, foo.eggs, foo.spam, zz1]
    
    # Nonexisting event type is ok
    assert foo.get_event_handlers('y') == []
    
    # No labels allowed
    with raises(ValueError):
        foo.get_event_handlers('x:a')


def test_that_methods_starting_with_on_are_not_autoconverted():
    # There is also a warning, but seems a bit of a fuzz to test
    class Foo(event.HasEvents):
        def on_foo(self, *events):
            pass
        @event.connect('bar')
        def on_bar(self, *events):
            pass
    
    foo = Foo()
    assert isinstance(foo.on_bar, event.Handler)
    assert not isinstance(foo.on_foo, event.Handler)


def test_collect_classes():
    skip('we did not go the metaclass way')  # Not if we don't use the meta class
    class Foo123(event.HasEvents):
        pass
    class Bar456(event.HasEvents):
        pass
    
    assert Foo123 in event.HasEvents.CLASSES
    assert Bar456 in event.HasEvents.CLASSES


def test_emit():
    
    h = event.HasEvents()
    events = []
    @h.connect('foo', 'bar')
    def handler(*evts):
        events.extend(evts)
    
    h.emit('foo', {})
    h.emit('bar', {'x': 1, 'y': 2})
    h.emit('spam', {})  # not registered
    handler.handle_now()
    
    assert len(events) == 2
    for ev in events:
        assert isinstance(ev, dict)
        assert ev.source is h
    assert len(events[0]) == 2
    assert len(events[1]) == 4
    assert events[0].type == 'foo'
    assert events[1].type == 'bar'
    assert events[1].x == 1
    assert events[1]['y'] == 2
    
    # Fail
    with raises(ValueError):
        h.emit('foo:a', {})
    with raises(TypeError):
        h.emit('foo', 4)
    with raises(TypeError):
        h.emit('foo', 'bla')


def test_registering_handlers():
    h = event.HasEvents()
    
    @h.connect('foo')
    def handler1(*evts):
        events.extend(evts)
    @h.connect('foo')
    def handler2(*evts):
        events.extend(evts)
    @h.connect('foo')
    def handler3(*evts):
        events.extend(evts)
    handler1.dispose()
    handler2.dispose()
    handler3.dispose()
    
    # Checks before we start
    assert h.get_event_types() == ['foo']
    assert h.get_event_handlers('foo') == []
    
    # Test adding handlers
    h._register_handler('foo', handler1)
    h._register_handler('foo:a', handler2)
    h._register_handler('foo:z', handler3)
    assert h.get_event_handlers('foo') == [handler2, handler1, handler3]
    
    # Unregestering one handler
    h.disconnect('foo', handler2)
    assert h.get_event_handlers('foo') == [handler1, handler3]
    
    # Reset
    h._register_handler('foo:a', handler2)
    assert h.get_event_handlers('foo') == [handler2, handler1, handler3]
    
    # Unregestering one handler + invalid label -> no unregister
    h.disconnect('foo:xx', handler2)
    assert h.get_event_handlers('foo') == [handler2, handler1, handler3]
    
    # Reset
    assert h.get_event_handlers('foo') == [handler2, handler1, handler3]
    
    # Unregestering one handler by label
    h.disconnect('foo:a')
    assert h.get_event_handlers('foo') == [handler1, handler3]
    
    # Reset
    h._register_handler('foo:a', handler2)
    assert h.get_event_handlers('foo') == [handler2, handler1, handler3]
    
    # Unregestering by type
    h.disconnect('foo')
    assert h.get_event_handlers('foo') == []


## Disposing ...

def test_disposing_method_handler1():
    """ handlers on object don't need cleaning. """ 
    
    class Foo(event.HasEvents):
        @event.connect('xx')
        def handle_xx(self, *events):
            pass
    
    foo = Foo()
    assert foo.get_event_handlers('xx')
    foo_ref = weakref.ref(foo)
    
    del foo
    gc.collect()
    assert foo_ref() is None


def test_disposing_method_handler2():
    """ handlers on object don't need cleaning but pending events need purge. """ 
    
    class Foo(event.HasEvents):
        @event.connect('xx')
        def handle_xx(self, *events):
            pass
    
    foo = Foo()
    assert foo.get_event_handlers('xx')
    foo.emit('xx', {})  # <---------
    foo_ref = weakref.ref(foo)
    
    del foo
    gc.collect()
    assert foo_ref() is not None  # pending event
    
    event.loop.iter()
    gc.collect()
    assert foo_ref() is None


def test_disposing_method_handler1():
    """ can call dispose with handlers on object. """ 
    
    class Foo(event.HasEvents):
        @event.connect('xx')
        def handle_xx(self, *events):
            pass
    
    foo = Foo()
    assert foo.get_event_handlers('xx')
    foo_ref = weakref.ref(foo)
    foo.dispose()  # <----
    
    event.loop.iter()
    
    del foo
    gc.collect()
    assert foo_ref() is None
    

def test_disposing_handler2():
    """ handlers outside object need cleaning. """ 
    
    def _():
        class Foo(event.HasEvents):
            pass
        foo = Foo()
        @foo.connect('xx')
        def handle_xx(*events):
            pass
        return foo
    
    foo = _()
    assert foo.get_event_handlers('xx')
    foo_ref = weakref.ref(foo)
    
    event.loop.iter()
    
    del foo
    gc.collect()
    assert foo_ref() is None


def test_disposing_handler3():
    """ handlers outside object need cleaning. """ 
    
    class Foo(event.HasEvents):
        pass
    foo = Foo()
    
    @foo.connect('xx')
    def handle_xx(*events):
        pass
    foo_ref = weakref.ref(foo)
    assert foo.get_event_handlers('xx')
    
    event.loop.iter()
    
    del foo
    gc.collect()
    assert foo_ref() is not None  # the handler still has refs
    
    foo_ref().dispose()
    gc.collect()
    assert foo_ref() is None


def test_disposing_handler4():
    """ handlers outside object plus pending event need cleaning. """ 
    
    class Foo(event.HasEvents):
        pass
    foo = Foo()
    
    @foo.connect('xx')
    def handle_xx(*events):
        pass
    foo_ref = weakref.ref(foo)
    assert foo.get_event_handlers('xx')
    
    event.loop.iter()
    
    foo.emit('xx', {})  # <---------
    
    del foo
    gc.collect()
    assert foo_ref() is not None  # the handler still has refs
    
    foo_ref().dispose()
    gc.collect()
    assert foo_ref() is not None  # pending event hold a ref
    
    handle_xx.handle_now()
    gc.collect()
    assert foo_ref() is None


def test_disposing_emitter():
    """ Emitters on object don't need cleaning. """ 
    
    class Foo(event.HasEvents):
        @event.prop
        def bar(self, v=0):
            return v
        
        @event.readonly
        def spam(self, v=0):
            return v
        
        @event.emitter
        def eggs(self, x):
            return {}
    
    foo = Foo()
    foo_ref = weakref.ref(foo)
    
    event.loop.iter()
    
    del foo
    gc.collect()
    assert foo_ref() is None


run_tests_if_main()
