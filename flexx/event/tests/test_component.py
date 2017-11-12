""" Tests for the Component class itself
"""

from flexx.util.testing import run_tests_if_main, skipif, skip, raises
from flexx.event._both_tester import run_in_both, this_is_js

from flexx.event import mutate_array, Dict
from flexx import event

loop = event.loop


class Comp(event.Component):
    pass


class Foo(event.Component):
    
    spam = 3
    eggs = [1, 2, 3]
    
    a_prop = event.AnyProp(settable=True)


class FooSubclass(Foo):
    pass


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
    

@run_in_both(FooSubclass)
def test_component_id1():
    """
    ? Foo
    ? FooSubclass
    """
    f = Foo()
    print(f._id)
    f = FooSubclass()
    print(f._id)


@run_in_both(FooSubclass, js=False)
def test_component_id2():
    """
    true
    true
    """
    f = Foo()
    print(f._id in str(f))
    f = FooSubclass()
    print(f._id in str(f))


@run_in_both(Foo, Bar, Comp)
def test_component_class_attributes1():
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


@run_in_both(Foo)
def test_component_class_attributes2():
    """
    3
    [1, 2, 3]
    """
    f = Foo()
    print(f.spam)
    print(f.eggs)


@run_in_both(FooSubclass)
def test_component_class_attributes3():
    """
    3
    [1, 2, 3]
    """
    f = FooSubclass()
    print(f.spam)
    print(f.eggs)


class CompWithInit1(event.Component):
    
    def init(self, a, b=3):
        print('i', a, b)

@run_in_both(CompWithInit1)
def test_component_init():
    """
    i 1 2
    i 1 3
    """
    CompWithInit1(1, 2)
    CompWithInit1(1)


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



class Foo2(event.Component):
    
    @event.reaction('!x')
    def spam(self, *events):
        pass
    
    @event.reaction('!x')
    def eggs(self, *events):
        pass


@run_in_both(Foo2)
def test_get_event_handlers():
    """
    ['bar', 'eggs', 'spam']
    ['zz2', 'bar', 'eggs', 'spam', 'zz1']
    []
    fail ValueError
    """
    
    foo = Foo2()
    
    def bar(*events):
        pass
    bar = foo.reaction('!x', bar)
    
    # sorted by label name
    print([r.get_name() for r in foo.get_event_handlers('x')])
    
    def zz1(*events):
        pass
    def zz2(*events):
        pass
    zz1 = foo.reaction('!x', zz1)
    zz2 = foo.reaction('!x:a', zz2)
    
    # sorted by label name
    print([r.get_name() for r in foo.get_event_handlers('x')])
    
    # Nonexisting event type is ok
    print([r.get_name() for r in foo.get_event_handlers('y')])
    
    # No labels allowed
    try:
        foo.get_event_handlers('x:a')
    except ValueError:
        print('fail ValueError')


def test_that_methods_starting_with_on_are_not_autoconverted():
    # Because we did that at some point
    
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


@run_in_both(Foo)
def test_component_fails():
    """
    fail TypeError
    fail AttributeError
    fail RuntimeError
    fail ValueError
    """
    
    f = Foo()
    loop._processing_action = True
    
    try:
        f._mutate(3, 3)  # prop name must be str
    except TypeError:
        print('fail TypeError')
    
    try:
        f._mutate('invalidpropname', 3)  # prop name invalid
    except AttributeError:
        print('fail AttributeError')
    
    f.reaction('!foo', lambda: None)  # Ok
        
    try:
        f.reaction(lambda: None)  # Component.reaction cannot be implicit
    except RuntimeError:
        print('fail RuntimeError')
    
    try:
        f.reaction(42, lambda: None)  # 42 is not a string
    except ValueError:
        print('fail ValueError')


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
    
    # Wont add twice
    c._register_reaction('foo', handler1)
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


@run_in_both()
def test_mutate_array1():
    """
    [1, 2, 5, 6]
    [1, 2, 3, 3, 4, 4, 5, 6]
    [1, 2, 3, 4, 5, 6]
    [1, 2, 3, 4, 50, 60]
    []
    """
    a = []
    
    mutate_array(a, dict(mutation='set', index=0, objects=[1,2,5,6]))
    print(a)
    
    mutate_array(a, dict(mutation='insert', index=2, objects=[3, 3, 4, 4]))
    print(a)
    
    mutate_array(a, dict(mutation='remove', index=3, objects=2))
    print(a)
    
    mutate_array(a, dict(mutation='replace', index=4, objects=[50, 60]))
    print(a)
    
    mutate_array(a, dict(mutation='set', index=0, objects=[]))
    print(a)


@run_in_both(js=False)
def test_mutate_array2():
    """
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
    [0, 1, 2, 0, 0, 0, 0, 7, 8, 9, 10, 11]
    [0, 1, 2, 3, 4, 5, 0, 0, 8, 9, 0, 0]
    """
    
    try:
        import numpy as np
    except ImportError:
        skip('No numpy')
    
    a = np.arange(12)
    print(list(a.flat))
    
    mutate_array(a, dict(mutation='replace', index=3, objects=np.zeros((4,))))
    print(list(a.flat))
    
    a = np.arange(12)
    a.shape = 3, 4
    
    mutate_array(a, dict(mutation='replace', index=(1, 2), objects=np.zeros((2,2))))
    print(list(a.flat))


run_tests_if_main()
