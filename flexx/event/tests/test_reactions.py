"""
Test reactions.
"""

import gc
import sys
import weakref

from flexx.util.testing import run_tests_if_main, skipif, skip, raises
from flexx.event._both_tester import run_in_both, this_is_js
from flexx.util.logging import capture_log

from flexx import event

loop = event.loop


class MyObject1(event.Component):
    
    @event.reaction('!a')
    def r1(self, *events):
        print('r1 ' + ' '.join([ev.type for ev in events]))
    
    @event.reaction('!a', '!b')
    def r2(self, *events):
        print('r2 ' + ' '.join([ev.type for ev in events]))
    
    @event.reaction('!c')
    def r3(self, *events):
        pass


## Order

@run_in_both(MyObject1)
def test_reaction_order1():
    """
    r1 a a
    r2 a a
    r1 a a
    r2 a a
    """
    m = MyObject1()
    
    # since there is a reaction for c, the a events cannot join
    with loop:
        m.emit('a', {})
        m.emit('a', {})
        m.emit('c', {})
        m.emit('c', {})
        m.emit('a', {})
        m.emit('a', {})


@run_in_both(MyObject1)
def test_reaction_order2():
    """
    r1 a a
    r2 a a b b a a
    r1 a a
    r1 a
    r2 a
    """
    m = MyObject1()
    
    # for r1, the events cannot join, but they can for b
    with loop:
        m.emit('a', {})
        m.emit('a', {})
        m.emit('b', {})
        m.emit('b', {})
        m.emit('a', {})
        m.emit('a', {})
        m.emit('c', {})  # but this breaks it
        m.emit('a', {})


@run_in_both(MyObject1)
def test_reaction_order3():
    """
    r2 b a a
    r1 a a
    """
    m = MyObject1()
    
    # in all of the above r1 went first, because of its name.
    # now r2 is "triggered" first
    with loop:
        m.emit('b', {})
        m.emit('a', {})
        m.emit('a', {})


@run_in_both(MyObject1)
def test_reaction_order4():
    """
    r2 b a a
    r1 a a
    """
    m = MyObject1()
    
    # in all of the above r1 went first, because of its name.
    # now r2 is "triggered" first
    with loop:
        m.emit('b', {})
        m.emit('a', {})
        m.emit('a', {})


## Labels

class MyObject_labeled(event.Component):
    
    @event.reaction('!a')
    def r1(self, *events):
        print('r1 ' + ' '.join([ev.type for ev in events]))
    
    @event.reaction('!a:b')
    def r2(self, *events):
        print('r2 ' + ' '.join([ev.type for ev in events]))
    
    @event.reaction('!a:a')
    def r3(self, *events):
        print('r3 ' + ' '.join([ev.type for ev in events]))


@run_in_both(MyObject_labeled)
def test_reaction_labels1():
    """
    r3 a a
    r2 a a
    r1 a a
    """
    m = MyObject_labeled()
    
    # in all of the above r1 went first, because of its name.
    # now r2 is "triggered" first
    with loop:
        m.emit('a', {})
        m.emit('a', {})


## Init order

class MyObject_init(event.Component):
    
    foo = event.IntProp(settable=True)
    bar = event.IntProp(7, settable=True)
    
    @event.reaction('foo', 'bar')
    def _report(self, *events):
        print('r ' + ', '.join(['%s:%i->%i' % (ev.type, ev.old_value, ev.new_value) for ev in events]))


@run_in_both(MyObject_init)
def test_reacion_init1():
    """
    0 7
    iter
    r foo:0->0, bar:7->7
    0 7
    end
    """
    # order foo bar is because of order of connection strings
    m = MyObject_init()
    print(m.foo, m.bar)
    print('iter')
    loop.iter()
    print(m.foo, m.bar)
    print('end')


@run_in_both(MyObject_init, js=False)  # todo: kwargs
def test_reacion_init2():
    """
    0 7
    iter
    r foo:0->0, bar:7->7, bar:7->4, foo:0->4
    4 4
    end
    """
    # Order of first two is determined by order of connection strings
    # the next two by the property name
    m = MyObject_init(foo=4, bar=4)
    print(m.foo, m.bar)
    print('iter')
    loop.iter()
    print(m.foo, m.bar)
    print('end')


@run_in_both(MyObject_init)
def test_reacion_init3():
    """
    0 7
    iter
    r foo:0->0, bar:7->7, foo:0->2, bar:7->2
    2 2
    end
    """
    # order foo bar is because of order of connection strings
    m = MyObject_init()
    m.set_foo(2)
    m.set_bar(2)
    print(m.foo, m.bar)
    print('iter')
    loop.iter()
    print(m.foo, m.bar)
    print('end')


@run_in_both(MyObject_init, js=False)  # todo: kwargs
def test_reacion_init4():
    """
    0 7
    iter
    r foo:0->0, bar:7->7, bar:7->4, foo:0->4, foo:4->2, bar:4->2
    2 2
    end
    """
    # Order of first two is determined by order of connection strings
    # the next two by the property name, the next two by order of actions.
    m = MyObject_init(foo=4, bar=4)
    m.set_foo(2)
    m.set_bar(2)
    print(m.foo, m.bar)
    print('iter')
    loop.iter()
    print(m.foo, m.bar)
    print('end')


## Meta-ish tests that are similar for property/emitter/action/reaction


@run_in_both(MyObject1)
def test_reaction_meta():
    """
    True
    r1
    [['!a', ['a:r1']]]
    [['!a', ['a:r2']], ['!b', ['b:r2']]]
    """
    m = MyObject1()
    
    print(hasattr(m.r1, 'dispose'))
    print(m.r1.get_name())
    print([list(x) for x in m.r1.get_connection_info()])  # tuple-> list
    print([list(x) for x in m.r2.get_connection_info()])


@run_in_both(MyObject1)
def test_reaction_not_settable():
    """
    fail AttributeError
    """
    
    m = MyObject1()
    
    try:
        m.r1 = 3
    except AttributeError:
        print('fail AttributeError')
    
    # We cannot prevent deletion in JS, otherwise we cannot overload


def test_reaction_python_only():
    
    m = MyObject1()
    
    # Reaction decorator needs proper callable and connection strings
    with raises(TypeError):
        event.reaction(3)
    with raises(TypeError):
        event.reaction(isinstance)
    
    # Check type of the instance attribute
    assert isinstance(m.r1, event._reaction.Reaction)
    
    # Cannot set or delete a reaction
    with raises(AttributeError):
        m.r1 = 3
    with raises(AttributeError):
        del m.r1
    
    # Repr and docs
    assert 'reaction' in repr(m.__class__.r1).lower()
    assert 'reaction' in repr(m.r1).lower()
    assert 'r1' in repr(m.r1)


run_tests_if_main()
