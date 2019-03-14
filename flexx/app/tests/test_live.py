""" Test components live.
"""

import gc
import weakref
import asyncio

from pscript import this_is_js

from flexx import app, event

from flexx.util.testing import run_tests_if_main, raises, skip, skipif
from flexx.app.live_tester import run_live, roundtrip, launch

from flexx.event import loop


def setup_module():
    app.manager._clear_old_pending_sessions(1)


class PyComponentA(app.PyComponent):

    foo = event.IntProp(settable=True)
    sub = event.ComponentProp(settable=True)

    @event.action
    def greet(self, msg):
        print('hi', msg)

    @event.emitter
    def bar_event(self, v):
        return dict(value=v)

    @event.reaction
    def _on_foo(self):
        if self.sub is not None:
            print('sub foo changed', self.sub.foo)

    @event.reaction('bar_event')
    def _on_bar(self, *events):
        print('got bar event', [ev.value for ev in events])


class JsComponentA(app.JsComponent):

    foo = event.IntProp(settable=True)
    sub = event.ComponentProp(settable=True)

    @event.action
    def greet(self, msg):
        print('hi', msg)

    @event.emitter
    def bar_event(self, v):
        return dict(value=v)

    @event.reaction
    def _on_foo(self):
        if self.sub is not None:
            print('sub foo changed', self.sub.foo)

    @event.reaction('bar_event')
    def _on_bar(self, *events):
        for ev in events:
            print('got bar event', ev.value)
        # Hard to guarantee that events from Py get handled in same iter
        #print('got bar event', [ev.value for ev in events])


class PyComponentC(PyComponentA):
    def init(self, foo):
        print('init')
        self.set_foo(foo)


class JsComponentC(JsComponentA):
    def init(self, foo):
        print('init')
        self.set_foo(foo)


## PyComponent basics

@run_live
async def test_pycomponent_action1():
    """
    hi foo
    hi bar
    hi spam
    ----------
    """
    c, s = launch(PyComponentA)
    c.greet('foo')
    c.greet('bar')
    s.send_command('INVOKE', c.id, 'greet', ["spam"])
    await roundtrip(s)


@run_live
async def test_pycomponent_action_chained():
    """
    hi foo
    hi bar
    hi xx
    ----------
    """
    c, s = launch(PyComponentA)
    c.greet('foo').greet('bar').greet('xx')
    await roundtrip(s)


@run_live
async def test_pycomponent_action2():
    """
    hi foo
    hi bar
    hi spam
    ----------
    """
    c1, s = launch(PyComponentA)

    with c1:
        c = PyComponentA()
    assert c.session is s


    c.greet('foo')
    c.greet('bar')
    s.send_command('INVOKE', c.id, 'greet', ["spam"])
    await roundtrip(s)


@run_live
async def test_pycomponent_prop1():
    """
    0
    3
    3
    ----------
    0
    3
    """
    c, s = launch(PyComponentA)

    c.set_foo(3)
    print(c.foo)
    s.send_command('EVAL', c.id, 'foo')
    loop.iter()
    print(c.foo)  # this will mutate foo
    await roundtrip(s)
    print(c.foo)
    s.send_command('EVAL', c.id, 'foo')
    await roundtrip(s)


@run_live
async def test_pycomponent_reaction1():
    """
    0
    sub foo changed 0
    0
    sub foo changed 3
    3
    ----------
    """
    c1, s = launch(PyComponentA)

    with c1:
        c2 = PyComponentA()  # PyComponent sub
    c1.set_sub(c2)

    print(c2.foo)
    loop.iter()

    c2.set_foo(3)

    print(c2.foo)
    loop.iter()
    print(c2.foo)

    await roundtrip(s)


@run_live
async def test_pycomponent_reaction2():
    """
    0
    sub foo changed 0
    0
    sub foo changed 3
    3
    ----------
    """
    c1, s = launch(PyComponentA)

    with c1:
        c2 = JsComponentA()  # JsComponent sub
    c1.set_sub(c2)

    print(c2.foo)
    await roundtrip(s)

    c2.set_foo(3)

    print(c2.foo)
    await roundtrip(s)
    print(c2.foo)

    await roundtrip(s)


@run_live
async def test_pycomponent_emitter1():
    """
    got bar event [6, 7]
    got bar event [8, 9]
    ----------
    ? Cannot use emitter
    ? Cannot use emitter
    ? Cannot use emitter
    ? Cannot use emitter
    """
    c, s = launch(PyComponentA)

    c.bar_event(6)
    c.bar_event(7)
    await roundtrip(s)

    c.bar_event(8)
    c.bar_event(9)
    await roundtrip(s)

    s.send_command('INVOKE', c.id, 'bar_event', [16])
    s.send_command('INVOKE', c.id, 'bar_event', [17])
    await roundtrip(s)

    s.send_command('INVOKE', c.id, 'bar_event', [18])
    s.send_command('INVOKE', c.id, 'bar_event', [19])
    await roundtrip(s)


@run_live
async def test_pycomponent_init1():
    """
    init
    init
    10
    20
    20
    ----------
    """
    c1, s = launch(app.PyComponent)

    with c1:
        c2 = PyComponentA(foo=10)
        c3 = PyComponentC(20)
        c4 = PyComponentC(20, foo=10)  # What happens in init takes preference

    await roundtrip(s)

    print(c2.foo)
    print(c3.foo)
    print(c4.foo)


## JsComponent basics


@run_live
async def test_jscomponent_action1():
    """
    ----------
    hi foo
    hi bar
    hi spam
    """
    c, s = launch(JsComponentA)

    c.greet('foo')
    c.greet('bar')
    s.send_command('INVOKE', c.id, 'greet', ["spam"])
    await roundtrip(s)
    await roundtrip(s)


@run_live
async def test_jscomponent_action2():
    """
    ----------
    hi foo
    hi bar
    hi spam
    """
    c1, s = launch(JsComponentA)

    with c1:
        c = JsComponentA()
    assert c.session is s

    c.greet('foo')
    c.greet('bar')
    s.send_command('INVOKE', c.id, 'greet', ["spam"])
    await roundtrip(s)
    await roundtrip(s)


@run_live
async def test_jscomponent_prop1():
    """
    0
    0
    3
    ----------
    0
    3
    """
    c, s = launch(JsComponentA)

    # Note: set_foo() immediately sends an INVOKE command. If the
    # subsequent (now commented) EVAL command is not handled in the same
    # event loop iter, the value will already have been updated.

    s.send_command('EVAL', c.id, 'foo')
    c.set_foo(3)
    print(c.foo)
    # s.send_command('EVAL', c.id, 'foo')
    loop.iter()
    print(c.foo)  # still not set
    await roundtrip(s)
    print(c.foo)
    s.send_command('EVAL', c.id, 'foo')
    await roundtrip(s)


@run_live
async def test_jscomponent_reaction1():
    """
    0
    0
    3
    ----------
    sub foo changed 0
    sub foo changed 3
    """
    c1, s = launch(JsComponentA)

    with c1:
        c2 = PyComponentA()  # PyComponent sub
    c1.set_sub(c2)

    print(c2.foo)
    await roundtrip(s)

    c2.set_foo(3)

    print(c2.foo)
    await roundtrip(s)
    print(c2.foo)

    await roundtrip(s)


@run_live
async def test_jscomponent_reaction2():
    """
    0
    0
    3
    ----------
    sub foo changed 0
    sub foo changed 3
    """
    c1, s = launch(JsComponentA)

    with c1:
        c2 = JsComponentA()  # JsComponent sub
    c1.set_sub(c2)

    print(c2.foo)
    await roundtrip(s)

    c2.set_foo(3)

    print(c2.foo)
    await roundtrip(s)
    print(c2.foo)

    await roundtrip(s)


@run_live
async def test_jscomponent_emitter1():
    """
    ? Cannot use emitter
    ? Cannot use emitter
    ? Cannot use emitter
    ? Cannot use emitter
    ----------
    got bar event 16
    got bar event 17
    got bar event 18
    got bar event 19
    """
    c, s = launch(JsComponentA)

    c.bar_event(6)
    c.bar_event(7)
    await roundtrip(s)

    c.bar_event(8)
    c.bar_event(9)
    await roundtrip(s)

    s.send_command('INVOKE', c.id, 'bar_event', [16])
    s.send_command('INVOKE', c.id, 'bar_event', [17])
    await roundtrip(s)

    s.send_command('INVOKE', c.id, 'bar_event', [18])
    s.send_command('INVOKE', c.id, 'bar_event', [19])
    await roundtrip(s)


@run_live
async def test_jscomponent_init1():
    """
    0
    0
    0
    10
    20
    20
    ----------
    init
    init
    """
    # This test is important. We have plenty of tests that ensure that the init
    # args and kwargs work in both Python and JS variants of Component, but
    # instantiating a JsComponent in Python will have to communicate these!
    c1, s = launch(app.PyComponent)

    with c1:
        c2 = JsComponentA(foo=10)
        c3 = JsComponentC(20)
        c4 = JsComponentC(20, foo=10)  # What happens in init takes preference

    # Data is not yet synced
    print(c2.foo)
    print(c3.foo)
    print(c4.foo)

    await roundtrip(s)

    print(c2.foo)
    print(c3.foo)
    print(c4.foo)


## With sub components


class CreatingPyComponent(PyComponentA):

    def init(self):
        self._x = JsComponentA(foo=7)

    @event.action
    def apply_sub(self):
        self.set_sub(self._x)


class CreatingJsComponent(JsComponentA):

    def init(self):
        self._x = JsComponentA(foo=7)

    @event.action
    def apply_sub(self):
        self.set_sub(self._x)


@run_live
async def test_proxy_binding1():
    """
    sub foo changed 7
    7
    sub foo changed 7
    7
    ----------
    """
    # Get ref to JsComponent instantiated by a PyComponent

    c1, s = launch(app.PyComponent)

    with c1:
        c2 = CreatingPyComponent()  # PyComponent that has local JsComponent

    await roundtrip(s)
    assert c2.sub is None

    # Get access to the sub component
    c2.apply_sub()
    await roundtrip(s)

    c3 = c2.sub
    assert isinstance(c3, JsComponentA)
    print(c3.foo)

    # Get id of c3 and get rid of any references
    c3_id = c3.id
    c3_ref = weakref.ref(c3)
    c2.set_sub(None)
    for i in range(5):
        await roundtrip(s)
    del c3
    for i in range(5):
        await roundtrip(s)

    assert c3_ref() is not None  # because PyComponent has it

    # Get access to the sub component again (proxy thereof, really)
    c2.apply_sub()
    await roundtrip(s)
    c3 = c2.sub
    assert isinstance(c3, JsComponentA)
    assert c3.id == c3_id
    print(c3.foo)


@run_live
async def test_proxy_binding2():
    """
    7
    7
    ----------
    sub foo changed 7
    sub foo changed 7
    """
    # Get ref to JsComponent instantiated by a JsComponent,
    # drop that ref, re-get the proxy instance, and verify that its
    # a different instance representing the same object in JS

    c1, s = launch(app.PyComponent)

    with c1:
        c2 = CreatingJsComponent()  # JsComponent that has local JsComponent

    await roundtrip(s)
    assert c2.sub is None

    # Get access to the sub component
    c2.apply_sub()
    await roundtrip(s)
    await roundtrip(s)

    c3 = c2.sub
    assert isinstance(c3, JsComponentA)
    print(c3.foo)

    # Get id of c3 and get rid of any references
    id3 = id(c3)
    c3_ref = weakref.ref(c3)
    c3_id = c3.id
    c2.set_sub(None)
    for i in range(5):  # need a few roundtrips for session to drop c3
        await roundtrip(s)
    del c3
    for i in range(5):
        await roundtrip(s)
        gc.collect()

    assert c3_ref() is None  # Python dropped it, but JS still has the object!

    # Get access to the sub component again (proxy thereof, really)
    c2.apply_sub()
    await roundtrip(s)
    c3 = c2.sub
    assert isinstance(c3, JsComponentA)
    assert c3.id == c3_id
    print(c3.foo)


@skipif(True, reason='This test is flaky since early 2019')
@run_live
async def test_proxy_binding3():
    """
    sub foo changed 0
    sub foo changed 3
    sub foo changed 6
    sub foo changed 7
    ? Using stub component
    ? session does not know it
    ----------
    """
    # Test that local components only send events when there is a proxy,
    # and that when events are send anyway, warnings are shown

    c1, s = launch(PyComponentA)

    with c1:
        c2 = JsComponentA()  # JsComponent that has local JsComponent
    c1.set_sub(c2)
    id2 = c2.id

    # Change foo of c2
    c2.set_foo(3)
    await roundtrip(s)

    # Now, we're pretend that to drop the instance
    s.send_command('INVOKE', c2.id, '_flx_set_has_proxy', [False])
    await roundtrip(s)

    # We don't get the events anymore
    c2.set_foo(4)
    c2.set_foo(5)
    await roundtrip(s)

    # Re-establish
    s.send_command('INVOKE', c2.id, '_flx_set_has_proxy', [True])
    await roundtrip(s)

    # We get these
    c2.set_foo(6)
    s.send_command('INVOKE', id2, 'set_foo', [7])  # same thing, really
    await roundtrip(s)

    # Now, we simulate destroying the proxy without JS knowing
    s._component_instances.pop(id2)

    # And then ... invoking an event will raise one error for not being able
    # to invoke in Python, and one for not being able to decode the "source"
    # of the event.
    s.send_command('INVOKE', id2, 'set_foo', [9])
    await roundtrip(s)


## Multi-session


class JsComponentB(app.JsComponent):

    sub1 = event.ComponentProp(settable=True)
    sub2 = event.ComponentProp(settable=True)

    @event.action
    def sub1_to_sub2(self):
        self.set_sub2(self.sub1)


@run_live
async def test_proxy_binding21():
    """
    14 None
    24 None
    24 24
    ----------
    14
    ? JsComponentA
    undefined
    ? JsComponentA
    undefined
    """
    # Test multiple sessions, and sharing objects

    c1, s1 = launch(JsComponentB)
    c2, s2 = launch(JsComponentB)

    with c1:
        c11 = JsComponentA()  # JsComponent that has local JsComponent
        c1.set_sub1(c11)

    with c2:
        c22 = JsComponentA()  # JsComponent that has local JsComponent
        c2.set_sub1(c22)
    await roundtrip(s1, s2)

    c11.set_foo(14)
    c22.set_foo(24)
    await roundtrip(s1, s2)

    print(c1.sub1 and c1.sub1.foo, c1.sub2 and c1.sub2.foo)
    s1.send_command('EVAL', c1.id, 'sub1.foo')
    await roundtrip(s1, s2)

    # So far, not much news, now break the universe ...

    c1.set_sub1(c2.sub1)
    await roundtrip(s1, s2)
    print(c1.sub1 and c1.sub1.foo, c1.sub2 and c1.sub2.foo)

    # In JS, c1.sub1 will be a stub
    s1.send_command('EVAL', c1.id, 'sub1.id')
    s1.send_command('EVAL', c1.id, 'sub1.foo')
    await roundtrip(s1, s2)

    # But we can still "handle" it
    c1.sub1_to_sub2()
    await roundtrip(s1, s2)

    # And now c1.sub2.foo has the value of c2.sub1.foo
    print(c1.sub1 and c1.sub1.foo, c1.sub2 and c1.sub2.foo)
    s1.send_command('EVAL', c1.id, 'sub1.id')
    s1.send_command('EVAL', c1.id, 'sub1.foo')
    await roundtrip(s1, s2)


@run_live
async def test_sharing_state_between_sessions():
    """
    7
    7
    42
    42
    ----------
    7
    7
    42
    42
    """
    # Test sharing state between multiple sessions

    class SharedComponent(event.Component):
        foo = event.IntProp(0, settable=True)

    shared = SharedComponent()

    # This lambda thingy at a PyComponent is the magic to share state
    # Note that this needs to be setup for each property. It would be nice
    # to really share a component (proxy), but this would mean that a
    # PyComponent could have multiple sessions, which would complicate things
    # too much to be worthwhile.
    c1 = app.App(PyComponentA, foo=lambda:shared.foo).launch()
    c2 = app.App(PyComponentA, foo=lambda:shared.foo).launch()
    s1, s2 = c1.session, c2.session

    with c1:
        c11 = JsComponentA()
    with c2:
        c22 = JsComponentA()
    await roundtrip(s1, s2)

    shared.set_foo(7)
    await roundtrip(s1, s2)

    print(c1.foo)
    s1.send_command('EVAL', c1.id, 'foo')
    await roundtrip(s1, s2)
    print(c2.foo)
    s2.send_command('EVAL', c2.id, 'foo')

    shared.set_foo(42)
    await roundtrip(s1, s2)

    print(c1.foo)
    s1.send_command('EVAL', c1.id, 'foo')
    await roundtrip(s1, s2)
    print(c2.foo)
    s2.send_command('EVAL', c2.id, 'foo')

    await roundtrip(s1, s2)


class CreatingJsComponent2(app.JsComponent):

    sub = event.ComponentProp(settable=True)

    @event.action
    def create_sub(self):
        with self:
            c = CreatingJsComponent2()
            self.set_sub(c)


@run_live
async def test_component_id_uniqueness():
    """
    JsComponentB_1
    CreatingJsComponent2_2
    CreatingJsComponent2_2js
    JsComponentB_1
    CreatingJsComponent2_2
    CreatingJsComponent2_2js
    3
    6
    3
    ----------
    JsComponentB_1
    CreatingJsComponent2_2
    CreatingJsComponent2_2js
    JsComponentB_1
    CreatingJsComponent2_2
    CreatingJsComponent2_2js
    """
    # Test uniqueness of component id's

    c1, s1 = launch(JsComponentB)
    c2, s2 = launch(JsComponentB)

    with c1:
        c11 = CreatingJsComponent2()  # JsComponent that has local JsComponent
        c11.create_sub()
        c11.create_sub()
    with c2:
        c22 = CreatingJsComponent2()  # JsComponent that has local JsComponent
        c22.create_sub()
        c22.create_sub()
    await roundtrip(s1, s2)

    cc = [c1, c11, c11.sub, c2, c22, c22.sub]

    for c in cc:
        print(c.id)
        c.session.send_command('EVAL', c.id, 'id')
        await roundtrip(s1, s2)

    # That was not very unique though
    s = set()
    for c in cc:
        s.add(c.id)
    print(len(s))

    # But this is
    s = set()
    for c in cc:
        s.add(c.uid)
    print(len(s))

    # And this should be too
    s = set()
    for c in [c1, c11, c11.sub]:
        s.add(c.id.split('_')[-1])
    print(len(s))


##

run_tests_if_main()
