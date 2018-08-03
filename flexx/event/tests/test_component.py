""" Tests for the Component class itself
"""

from flexx.util.testing import run_tests_if_main, skipif, skip, raises
from flexx.event.both_tester import run_in_both, this_is_js
from flexx.event._js import create_js_component_class

from flexx.event import mutate_array, Dict
from flexx import event

loop = event.loop

Component = event.Component


class Foo(event.Component):

    an_attr = event.Attribute()

    spam = 3
    eggs = [1, 2, 3]

    a_prop = event.AnyProp(settable=True)

    def init(self):
        super().init()
        self._an_attr = 54

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


class Bar2(Bar):
    pass


@run_in_both(FooSubclass)
def test_component_id1():
    """
    ? Component
    ? Foo
    ? FooSubclass
    """
    f = Component()
    print(f.id)
    f = Foo()
    print(f.id)
    f = FooSubclass()
    print(f.id)


@run_in_both(FooSubclass, js=False)
def test_component_id2():
    """
    true
    true
    true
    """
    f = Component()
    print(f.id in str(f))
    f = Foo()
    print(f.id in str(f))
    f = FooSubclass()
    print(f.id in str(f))


@run_in_both(Foo)
def test_component_pending_events():
    """
    2
    None
    """

    f = Foo()
    print(len(f._Component__pending_events))  # The event for foo, plus None-mark

    loop.iter()

    # Its important that we dont keep collecting events, for obvious reasons
    print(f._Component__pending_events)


@run_in_both(Foo, Bar)
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
    c = Component()
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
def test_component_init1():
    """
    i 1 2
    i 1 3
    """
    CompWithInit1(1, 2)
    CompWithInit1(1)


class CompWithInit2(event.Component):

    foo1 = event.IntProp(1)
    foo2 = event.IntProp(2, settable=True)
    foo3 = event.IntProp(3)

    def init(self, set_foos):
        if set_foos:
            self._mutate_foo1(11)
            self.set_foo2(12)
            self.set_foo3(13)

    @event.action
    def set_foo3(self, v):
        self._mutate_foo3(v+100)


@run_in_both(CompWithInit2)
def test_component_init2():
    """
    1 2 103
    11 12 113
    6 7 108
    11 12 113
    12
    99
    """
    m = CompWithInit2(False)
    print(m.foo1, m.foo2, m.foo3)

    m = CompWithInit2(True)
    print(m.foo1, m.foo2, m.foo3)

    m = CompWithInit2(False, foo1=6, foo2=7, foo3=8)
    print(m.foo1, m.foo2, m.foo3)

    m = CompWithInit2(True, foo1=6, foo2=7, foo3=8)
    print(m.foo1, m.foo2, m.foo3)

    # This works, because when a componentn is "active" it allows mutations
    m.set_foo2(99)
    print(m.foo2)

    with m:
        m.set_foo2(99)
    print(m.foo2)


class CompWithInit3(event.Component):

    sub = event.ComponentProp(settable=True)

    @event.reaction('sub.a_prop')
    def _on_sub(self, *events):
        for ev in events:
            print('sub prop changed', ev.new_value)

@run_in_both(CompWithInit3, Foo)
def test_component_init3():
    """
    sub prop changed 7
    sub prop changed 9
    """
    # Verify that reconnect events are handled ok when applying events in init

    f1 = Foo(a_prop=7)
    f2 = Foo(a_prop=8)

    c = CompWithInit3(sub=f1)

    # Simulate that we're in a component's init
    with c:
        c.set_sub(f2)

    f2.set_a_prop(9)

    # In the iter, the pending events will be flushed. One of these events
    # is the changed sub. We don't want to reconnect for properties that
    # did not change (because that's a waste of CPU cycles), but we not miss
    # any changes.
    loop.iter()


class CompWithInit4(event.Component):

    a_prop = event.IntProp(settable=True)

    def init(self, other, value):
        self.set_a_prop(value)
        other.set_a_prop(value)

    @event.action
    def create(self, other, value):
        self.set_a_prop(value)
        CompWithInit4(other, value)

@run_in_both(CompWithInit4, Foo)
def test_component_init4():
    """
    0 8
    8 8
    0 9
    9 9
    """
    # Verify that the behavior of an init() (can mutate self, but not other
    # components) is consistent, also when instantiated from an action.

    c1 = Foo(a_prop=0)
    c2 = Foo(a_prop=0)
    c3 = CompWithInit4(c1, 8)

    print(c1.a_prop, c3.a_prop)

    loop.iter()
    print(c1.a_prop, c3.a_prop)

    c3.create(c2, 9)
    loop.iter()

    print(c2.a_prop, c3.a_prop)

    loop.iter()
    print(c2.a_prop, c3.a_prop)


@run_in_both(Foo)
def test_component_instance_attributes1():
    """
    ? Component
    54
    ? cannot set
    ? attribute, not a property
    """

    c = Component()
    print(c.id)
    c = Foo()
    print(c.an_attr)
    try:
        c.an_attr = 0
    except Exception as err:
        print(err)

    try:
        Foo(an_attr=3)
    except AttributeError as err:
        print(err)


def test_component_instance_attributes2():  # Py only

    with raises(TypeError):
        class X(Component):
            a = event.Attribute(doc=3)


@run_in_both(Foo, Bar)
def test_component_event_types():
    """
    []
    ['a_prop']
    ['a_emitter', 'a_prop']
    """

    c = Component()
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
    class Foo3(event.Component):

        def on_foo(self, *events):
            pass

        @event.reaction('bar')
        def on_bar(self, *events):
            pass

    foo = Foo3()
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


@run_in_both(Component)
def test_registering_handlers():
    """
    ok
    """

    c = Component()

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


class CompCheckActive(event.Component):

    def init(self, do_iter=False):
        if do_iter:
            loop.iter()
        else:
            ac = loop.get_active_components()
            print('active', len(ac), ac[-2].a_prop)


@run_in_both(Foo, CompCheckActive)
def test_component_active1():
    """
    0
    active 2 7
    active 2 42
    0
    ? RuntimeError
    ? RuntimeError
    0
    """
    print(len(loop.get_active_components()))

    f = Foo(a_prop=7)
    with f:
        CompCheckActive()

    f.set_a_prop(42)
    loop.iter()
    with f:
        CompCheckActive()

    print(len(loop.get_active_components()))
    loop.iter()

    # Invoke error (once for newly created component, once for f
    with f:
        CompCheckActive(True)

    print(len(loop.get_active_components()))


@run_in_both(Foo, Bar)
def test_component_active2():
    """
    None
    ? Foo
    ? Bar
    ? Foo
    None
    """
    f = Foo()
    b = Bar()

    print(loop.get_active_component())
    with f:
        print(loop.get_active_component().id)
        with b:
            print(loop.get_active_component().id)
        print(loop.get_active_component().id)
    print(loop.get_active_component())


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


def test_produced_js():
    js1 = create_js_component_class(Bar, 'Bar')
    js2 = create_js_component_class(Bar2, 'Bar2')

    assert '__properties__ = ["a_prop"]' in js1
    assert '__properties__ = ["a_prop"]' in js2
    assert js1.count('a_prop') >= 3
    assert js2.count('a_prop') == 1

    assert '__actions__ = ["a_action"]' in js1
    assert '__actions__ = ["a_action"]' in js2
    assert js1.count('a_action') >= 2
    assert js2.count('a_action') == 1


run_tests_if_main()
