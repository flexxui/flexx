"""
Test event emitters.
"""

from flexx.util.testing import run_tests_if_main, skipif, skip, raises
from flexx.event._both_tester import run_in_both, this_is_js

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


@run_in_both(MyObject)
def test_emitter_fail():
    """
    fail TypeError
    fail TypeError
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
    # try:
    #     del m.foo
    # except AttributeError:
    #     print('fail AttributeError')
        

def test_emitter_python_only():
    
    m = MyObject()
    
    with raises(TypeError):
        event.emitter(3)  # emitter decorator needs callable
     
    with raises(RuntimeError):
        event.emitter(isinstance)  # emitter decorator needs callable
    
    with raises(AttributeError):
        del m.foo  # cannot delete an emitter


run_tests_if_main()
