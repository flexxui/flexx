"""
Test dispoing and the cleaning up of components and reaction objects.
"""

import gc
import weakref

from flexx.util.testing import run_tests_if_main, skipif, skip, raises
from flexx.event.both_tester import run_in_both, this_is_js

from flexx import event

loop = event.loop


## General behaviour

class MyComponent1(event.Component):

    foo = event.IntProp(settable=True)

    @event.reaction('foo')
    def on_foo(self, *events):
        pass

    def react2foo(self):
        self.foo + 1

    @event.reaction
    def on_foo_implicit(self):
        self.foo


class MyComponent2(event.Component):

    foo = event.IntProp(settable=True)

    @event.reaction('foo')
    def on_foo(self, *events):
        print([ev.new_value for ev in events])


class MyComponent3(event.Component):

    foo = event.IntProp(settable=True)

    @event.reaction
    def react2foo(self):
        print('foo is', self.foo)


class MyComponent4(event.Component):

    foo = event.IntProp(settable=True)
    other = event.ComponentProp(settable=True)

    @event.reaction('other.foo')
    def on_foo_explicit(self, *events):
        print('other foo is', events[-1].new_value)

    @event.reaction
    def on_foo_implicit(self):
        if self.other is not None:
            print('other foo is implicit', self.other.foo)


@run_in_both(MyComponent2)
def test_disposing_disconnects1():
    """
    [0, 1]
    xx
    [0, 1]
    xx
    """

    m = MyComponent2()
    m.set_foo(1)
    loop.iter()

    m.on_foo.dispose()
    m.set_foo(2)
    loop.iter()

    print('xx')

    m = MyComponent2()
    m.set_foo(1)
    loop.iter()

    m.dispose()
    m.set_foo(2)
    loop.iter()

    print('xx')


@run_in_both(MyComponent1)
def test_disposing_disconnects2():
    """
    ['x', 0, 1]
    xx
    ['x', 0, 1]
    xx
    """

    def func(*events):
        print(['x'] + [ev.new_value for ev in events])

    m = MyComponent1()
    handler = m.reaction(func, 'foo')
    m.set_foo(1)

    loop.iter()

    handler.dispose()
    m.set_foo(2)
    loop.iter()

    print('xx')

    m = MyComponent1()
    handler = m.reaction(func, 'foo')
    m.set_foo(1)
    loop.iter()

    m.dispose()
    m.set_foo(2)
    loop.iter()

    print('xx')


@run_in_both(MyComponent3)
def test_disposing_disconnects3():
    """
    foo is 1
    xx
    foo is 1
    xx
    """

    m = MyComponent3()
    m.set_foo(1)

    loop.iter()

    m.react2foo.dispose()
    m.set_foo(2)
    loop.iter()

    print('xx')

    m = MyComponent3()
    m.set_foo(1)
    loop.iter()

    m.dispose()
    m.set_foo(2)
    loop.iter()

    print('xx')


@run_in_both(MyComponent4)
def test_disposing_disconnects4():
    """
    other foo is implicit 0
    other foo is 1
    other foo is implicit 1
    other foo is 2
    xx
    other foo is implicit 0
    other foo is 1
    other foo is implicit 1
    xx
    """
    # This one tests where reaction and prop are on different objects

    m1 = MyComponent4()
    m2 = MyComponent4()
    m1.set_other(m2)
    loop.iter()

    m2.set_foo(1)
    loop.iter()

    m1.on_foo_implicit.dispose()
    m2.set_foo(2)
    loop.iter()

    m1.on_foo_explicit.dispose()
    m2.set_foo(3)
    loop.iter()

    print('xx')

    m1 = MyComponent4()
    m2 = MyComponent4()
    m1.set_other(m2)
    loop.iter()

    m2.set_foo(1)
    loop.iter()

    m2.dispose()
    m2.set_foo(2)
    loop.iter()

    print('xx')


## In JS ...


def run_in_js(*classes):
    return run_in_both(*classes, py=False, extra_nodejs_args=['--expose-gc'])


class MemCounter(event.Component):

    def reset(self):
        self.ref = process.memoryUsage().heapUsed

    def diff_in_mb(self):
        diff = process.memoryUsage().heapUsed - self.ref
        diff = int(diff/1048576 + 0.499)
        if diff == 0:
            return '0'
        elif diff < 0:
            return str(diff)
        else:
            return '+' + str(diff)


@run_in_js(MemCounter)
def test_disposing_js0():
    """
    +4
    0
    """

    mc = MemCounter()
    mc.reset()

    a = Array(512*1024)  # about 4 MiB
    print(mc.diff_in_mb())

    a = None
    gc()
    print(mc.diff_in_mb())


@run_in_js(MemCounter, MyComponent1)
def test_disposing_js1():  # The whole component + handler graph can be cleaned
    """
    +4
    0
    """

    m = MyComponent1()
    loop.iter()

    mc = MemCounter()
    mc.reset()

    m.on_foo.blob = Array(512*1024)  # about 4 MiB
    print(mc.diff_in_mb())

    m = None
    gc()
    print(mc.diff_in_mb())


@run_in_js(MemCounter, MyComponent1)
def test_disposing_js2():  # Disconnected handlers can be cleaned
    """
    +8
    +8
    +4
    0
    """

    def func(*events):
        pass

    m = MyComponent1()
    handler1 = m.reaction(func, '!foo')
    handler2 = m.reaction(func, '!foo')
    loop.iter()

    mc = MemCounter()
    mc.reset()

    handler1.blob = Array(512*1024)  # about 4 MiB
    handler2.blob = Array(512*1024)  # about 4 MiB
    print(mc.diff_in_mb())

    handler1 = None  # no effect, was not disposed
    gc()
    print(mc.diff_in_mb())

    handler2.dispose()
    handler2 = None
    gc()
    print(mc.diff_in_mb())

    m.dispose()  # but now handler1 will be cleared too
    gc()
    print(mc.diff_in_mb())


## In Python ... we can use weakrefs and gc

def test_reaction_dispose1():

    h = event.Component()

    @h.reaction('!x1', '!x2')
    def handler(*events):
        pass

    handler_ref = weakref.ref(handler)
    del handler
    gc.collect()
    assert handler_ref() is not None  # h is holding on

    handler_ref().dispose()
    gc.collect()
    assert handler_ref() is None


def test_reaction_dispose2():

    h = event.Component()

    @h.reaction('x1', 'x2')
    def handler(*events):
        pass

    handler_ref = weakref.ref(handler)
    del handler
    gc.collect()
    assert handler_ref() is not None  # h is holding on

    h.dispose()  # <=== only this line is different from test_dispose1()
    gc.collect()
    assert handler_ref() is None


def test_reaction_dispose3():
    # Test that connecting a "volatile" object to a static object works well
    # w.r.t. cleanup.

    relay = event.Component()

    class Foo:
        def bar(self, *events):
            pass

    foo = Foo()
    handler = relay.reaction(foo.bar, 'xx')

    handler_ref = weakref.ref(handler)
    foo_ref = weakref.ref(foo)

    del foo
    del handler

    gc.collect()

    assert foo_ref() is None
    assert handler_ref() is not None

    relay.emit('xx')
    loop.iter()
    gc.collect()

    assert foo_ref() is None
    assert handler_ref() is None


def test_disposing_method_handler1():
    """ handlers on object don't need cleaning. """

    class Foo(event.Component):
        @event.reaction('xx')
        def handle_xx(self, *events):
            pass

    foo = Foo()
    assert foo.get_event_handlers('xx')
    foo_ref = weakref.ref(foo)
    handler_ref = weakref.ref(foo.handle_xx)

    del foo

    # There is still an event in the queue, so cant cleanup now
    gc.collect()
    gc.collect()
    assert handler_ref() is not None
    assert foo_ref() is not None

    loop.iter()

    # But we can now
    gc.collect()
    assert handler_ref() is None
    assert foo_ref() is None


def test_disposing_method_handler2():
    """ handlers on object don't need cleaning but pending events need purge. """

    class Foo(event.Component):
        @event.reaction('xx')
        def handle_xx(self, *events):
            pass

    foo = Foo()
    assert foo.get_event_handlers('xx')
    foo.emit('xx', {})  # <---
    foo_ref = weakref.ref(foo)

    del foo
    gc.collect()
    assert foo_ref() is not None  # pending event

    loop.iter()
    gc.collect()
    assert foo_ref() is None


def test_disposing_method_handler3():
    """ can call dispose with handlers on object. """

    class Foo(event.Component):
        @event.reaction('xx')
        def handle_xx(self, *events):
            pass

    foo = Foo()
    assert foo.get_event_handlers('xx')
    foo_ref = weakref.ref(foo)
    foo.dispose()  # <----

    loop.iter()

    del foo
    gc.collect()
    assert foo_ref() is None


def test_disposing_handler2():
    """ handlers outside object need cleaning. """

    def _():
        class Foo(event.Component):
            pass
        foo = Foo()
        @foo.reaction('xx')
        def handle_xx(*events):
            pass
        return foo

    foo = _()
    assert foo.get_event_handlers('xx')
    foo_ref = weakref.ref(foo)

    loop.iter()

    del foo
    gc.collect()
    assert foo_ref() is None


def test_disposing_handler3():
    """ handlers outside object need cleaning. """

    class Foo(event.Component):
        pass
    foo = Foo()

    @foo.reaction('xx')
    def handle_xx(*events):
        pass
    foo_ref = weakref.ref(foo)
    assert foo.get_event_handlers('xx')

    loop.iter()

    del foo
    gc.collect()
    assert foo_ref() is not None  # the handler still has refs

    foo_ref().dispose()
    gc.collect()
    assert foo_ref() is None


def test_disposing_handler4():
    """ handlers outside object plus pending event need cleaning. """

    class Foo(event.Component):
        pass
    foo = Foo()

    @foo.reaction('xx')
    def handle_xx(*events):
        pass
    foo_ref = weakref.ref(foo)
    assert foo.get_event_handlers('xx')

    loop.iter()

    foo.emit('xx', {})  # <---

    del foo
    gc.collect()
    assert foo_ref() is not None  # the handler still has refs

    foo_ref().dispose()
    gc.collect()
    assert foo_ref() is not None  # pending event hold a ref

    loop.iter()
    gc.collect()
    assert foo_ref() is None



def test_disposing_handler5():
    """ explicit reactions need cleaning. """

    m1 = MyComponent4()
    m2 = MyComponent4()
    m1.set_other(m2)

    loop.iter()

    # Simply deleteing does not work, obviously
    m2_ref = weakref.ref(m2)
    del m2
    gc.collect()
    assert m2_ref() is not None

    # But disposing and removing ref works
    m2_ref().dispose()
    m1.set_other(None)
    loop.iter()
    gc.collect()
    assert m2_ref() is None


def test_disposing_handler6():
    """ explicit reactions need cleaning, done proper """

    class TestComponent1(event.Component):

        foo = event.IntProp()

    class TestComponent2(event.Component):

        def __init__(self, other):
            self.other = other
            super().__init__()

        @event.reaction('!other.foo')
        def handler1(self, *events):  # explicit
            print('explicit', events[-1].new_value)

        @event.reaction
        def handler2(self):  # implicit
            if self.other:
                print('implicit', self.other.foo)

    m1 = TestComponent1()  # the object we want to get rid of
    m2 = TestComponent2(m1)  # the object holding on to it
    loop.iter()

    loop.iter()

    # Simply deleting does not work, obviously
    m1_ref = weakref.ref(m1)
    del m1
    gc.collect()
    loop.iter()
    assert m1_ref() is not None

    # But disposing works
    m1_ref().dispose()
    m2.other = None
    loop.iter()
    gc.collect()
    assert m1_ref() is None


def test_disposing_emitter():
    """ Emitters on object don't need cleaning. """

    class Foo(event.Component):
        bar = event.AnyProp()
        spam = event.AnyProp()

        @event.emitter
        def eggs(self, x):
            return {}

    foo = Foo()
    foo_ref = weakref.ref(foo)

    loop.iter()

    del foo
    gc.collect()
    loop.iter()
    assert foo_ref() is None


run_tests_if_main()
