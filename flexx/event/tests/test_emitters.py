"""
Test event emitters.
"""

import sys

from flexx.util.testing import run_tests_if_main, skipif, skip, raises
from flexx.event.both_tester import run_in_both, this_is_js

from flexx import event

loop = event.loop


class MyObject(event.Component):

    @event.emitter
    def foo(self, v):
        if not isinstance(v, (int, float)):
            raise TypeError('Foo emitter expects a number.')
        return dict(value=float(v))

    @event.emitter
    def bar(self, v):
        return dict(value=float(v)+1)  # note plus 1

    @event.emitter
    def wrong(self, v):
        return float(v)  # does not return a dict

    @event.reaction('foo')
    def on_foo(self, *events):
        print('foo', ', '.join([str(ev.value) for ev in events]))

    @event.reaction('bar')
    def on_bar(self, *events):
        print('bar', ', '.join([str(ev.value) for ev in events]))


class MyObject2(MyObject):

    @event.emitter
    def bar(self, v):
        return super().bar(v + 10)


class MyObject3(MyObject):

    @event.reaction('foo', mode='greedy')
    def on_foo(self, *events):
        print('foo', ', '.join([str(ev.value) for ev in events]))

    @event.reaction('bar', mode='greedy')
    def on_bar(self, *events):
        print('bar', ', '.join([str(ev.value) for ev in events]))


@run_in_both(MyObject)
def test_emitter_ok():
    """
    foo 3.2
    foo 3.2, 3.3
    bar 4.8, 4.9
    bar 4.9
    """

    m = MyObject()

    with loop:
        m.foo(3.2)

    with loop:
        m.foo(3.2)
        m.foo(3.3)

    with loop:
        m.bar(3.8)
        m.bar(3.9)

    with loop:
        m.bar(3.9)


@run_in_both(MyObject2)
def test_emitter_overloading():  # and super()
    """
    bar 14.2, 15.5
    """
    m = MyObject2()
    with loop:
        m.bar(3.2)
        m.bar(4.5)


@run_in_both(MyObject)
def test_emitter_order():
    """
    foo 3.1, 3.2
    bar 6.3, 6.4
    foo 3.5, 3.6
    bar 6.7, 6.8
    bar 6.9, 6.9
    """
    m = MyObject()

    # Even though we emit foo 4 times between two event loop iterations,
    # they are only grouped as much as to preserve order. This was not
    # the case before the 2017 Flexx refactoring.
    with loop:
        m.foo(3.1)
        m.foo(3.2)
        m.bar(5.3)
        m.bar(5.4)
        m.foo(3.5)
        m.foo(3.6)
        m.bar(5.7)
        m.bar(5.8)

    # The last two occur after an event loop iter, so these cannot be grouped
    # with the previous.
    with loop:
        m.bar(5.9)
        m.bar(5.9)


@run_in_both(MyObject3)
def test_emitter_order_greedy():
    """
    foo 3.1, 3.2, 3.5, 3.6
    bar 6.3, 6.4, 6.7, 6.8
    bar 6.9, 6.9
    """
    m = MyObject3()

    # Even though we emit foo 4 times between two event loop iterations,
    # they are only grouped as much as to preserve order. This was not
    # the case before the 2017 Flexx refactoring.
    with loop:
        m.foo(3.1)
        m.foo(3.2)
        m.bar(5.3)
        m.bar(5.4)
        m.foo(3.5)
        m.foo(3.6)
        m.bar(5.7)
        m.bar(5.8)

    # The last two occur after an event loop iter, so these cannot be grouped
    # with the previous.
    with loop:
        m.bar(5.9)
        m.bar(5.9)


@run_in_both(MyObject)
def test_emitter_fail():
    """
    fail TypeError
    fail TypeError
    fail ValueError
    """

    m = MyObject()

    try:
        m.wrong(1.1)
    except TypeError:
        print('fail TypeError')

    try:
        m.foo('bla')
    except TypeError:
        print('fail TypeError')

    try:
        m.emit('bla:x')
    except ValueError:
        print('fail ValueError')


## Meta-ish tests that are similar for property/emitter/action/reaction


@run_in_both(MyObject)
def test_emitter_not_settable():
    """
    fail AttributeError
    """

    m = MyObject()

    try:
        m.foo = 3
    except AttributeError:
        print('fail AttributeError')

    # We cannot prevent deletion in JS, otherwise we cannot overload


def test_emitter_python_only():

    m = MyObject()

    # Emitter decorator needs proper callable
    with raises(TypeError):
        event.emitter(3)
    if '__pypy__' in sys.builtin_module_names:
        pass  # skip
    else:
        with raises(TypeError):
            event.emitter(isinstance)

    # Check type of the instance attribute
    assert isinstance(m.foo, event._emitter.Emitter)

    # Cannot set or delete an emitter
    with raises(AttributeError):
        m.foo = 3
    with raises(AttributeError):
        del m.foo

    # Repr and docs
    assert 'emitter' in repr(m.__class__.foo).lower()
    assert 'emitter' in repr(m.foo).lower()
    assert 'foo' in repr(m.foo)


run_tests_if_main()
