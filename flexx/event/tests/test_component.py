""" Tests for the Component class itself
"""

from flexx.util.testing import run_tests_if_main, skipif, skip, raises
from flexx.event._both_tester import run_in_both, this_is_js

from flexx import event

loop = event.loop


class Comp(event.Component):
    pass


class Foo(event.Component):
    
    a_prop = event.AnyProp(settable=True)


class Bar(event.Component):
    
    a_prop = event.AnyProp()
    
    @event.action
    def a_action(self):
        pass
    
    @event.reaction
    def a_reaction(self):
        pass
    
    @event.emitter
    def a_emitter(self, v):
        return {}
    
    @event.emitter  # deliberately define it twice
    def a_emitter(self, v):
        return {'x':1}
    

@run_in_both(Foo, Bar, Comp)
def test_component_class_attributes():
    """
    Component
    []
    []
    []
    []
    Foo
    ['set_a_prop']
    []
    []
    ['a_prop']
    Bar
    ['a_action']
    ['a_reaction']
    ['a_emitter']
    ['a_prop']
    """
    
    print('Component')
    c = Comp()
    print(c.__actions__)
    print(c.__reactions__)
    print(c.__emitters__)
    print(c.__properties__)
    
    print('Foo')
    c = Foo()
    print(c.__actions__)
    print(c.__reactions__)
    print(c.__emitters__)
    print(c.__properties__)
    
    print('Bar')
    c = Bar()
    print(c.__actions__)
    print(c.__reactions__)
    print(c.__emitters__)
    print(c.__properties__)


@run_in_both(Foo, Bar, Comp)
def test_component_event_types():
    """
    []
    ['a_prop']
    ['a_emitter', 'a_prop']
    """
    
    c = Comp()
    print(c.get_event_types())
    c = Foo()
    print(c.get_event_types())
    c = Bar()
    print(c.get_event_types())





def test_get_event_handlers():
    
    class Foo(event.Component):
        
        @event.reaction('x')
        def spam(self, *events):
            pass
        
        @event.reaction('x')
        def eggs(self, *events):
            pass
            
    foo = Foo()
    @foo.reaction('x')
    def bar(*events):
        pass
    
    # sorted by label name
    assert foo.get_event_handlers('x') == [bar, foo.eggs, foo.spam]
    
    @foo.reaction('x')
    def zz1(*events):
        pass
    @foo.reaction('x:a')
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
    class Foo(event.Component):
        
        def on_foo(self, *events):
            pass
        
        @event.reaction('bar')
        def on_bar(self, *events):
            pass
    
    foo = Foo()
    assert isinstance(foo.on_bar, event.Reaction)
    assert not isinstance(foo.on_foo, event.Reaction)


@run_in_both(Comp)
def test_registering_handlers():
    """
    ok
    """
    
    c = Comp()
    
    def handler1(*evts):
        events.extend(evts)
    
    def handler2(*evts):
        events.extend(evts)
    
    def handler3(*evts):
        events.extend(evts)
    
    handler1 = c.reaction('!foo', handler1)
    handler2 = c.reaction('!foo', handler2)
    handler3 = c.reaction('!foo', handler3)
    
    handler1.dispose()
    handler2.dispose()
    handler3.dispose()
    
    # Checks before we start
    assert c.get_event_types() == ['foo']
    assert c.get_event_handlers('foo') == []
    
    # Test adding handlers
    c._register_reaction('foo', handler1)
    c._register_reaction('foo:a', handler2)
    c._register_reaction('foo:z', handler3)
    assert c.get_event_handlers('foo') == [handler2, handler1, handler3]
    
    # Unregestering one handler
    c.disconnect('foo', handler2)
    assert c.get_event_handlers('foo') == [handler1, handler3]
    
    # Reset
    c._register_reaction('foo:a', handler2)
    assert c.get_event_handlers('foo') == [handler2, handler1, handler3]
    
    # Unregestering one handler + invalid label -> no unregister
    c.disconnect('foo:xx', handler2)
    assert c.get_event_handlers('foo') == [handler2, handler1, handler3]
    
    # Reset
    assert c.get_event_handlers('foo') == [handler2, handler1, handler3]
    
    # Unregestering one handler by label
    c.disconnect('foo:a')
    assert c.get_event_handlers('foo') == [handler1, handler3]
    
    # Reset
    c._register_reaction('foo:a', handler2)
    assert c.get_event_handlers('foo') == [handler2, handler1, handler3]
    
    # Unregestering by type
    c.disconnect('foo')
    assert c.get_event_handlers('foo') == []
    
    print('ok')


run_tests_if_main()
