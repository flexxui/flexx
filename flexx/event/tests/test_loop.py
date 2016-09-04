
from flexx.util.testing import run_tests_if_main, skipif, skip, raises

from flexx import event
from flexx.event._dict import isidentifier


class Foo(event.HasEvents):
    
    def __init__(self):
        super().__init__()
        self.r = []
    
    @event.connect('foo')
    def on_foo(self, *events):
        self.r.append(len(events))


def test_iter():
    
    foo = Foo()
    foo.emit('foo', {})
    assert len(foo.r) == 0
    event.loop.iter()
    assert len(foo.r) == 1
    assert foo.r[0] == 1
    
    foo = Foo()
    foo.emit('foo', {})
    foo.emit('foo', {})
    event.loop.iter()
    assert len(foo.r) == 1
    assert foo.r[0] == 2
    
    # Failing func call
    res = []
    def fail():
        res.append(1)
        1/0
    raises(ZeroDivisionError, fail)
    assert len(res) == 1
    
    # When handled by the loop, error is printed, but no fail
    event.loop.call_later(fail)
    event.loop.iter()
    assert len(res) == 2

def test_context():
    
    foo = Foo()
    with event.loop:
        foo.emit('foo', {})
    assert len(foo.r) == 1
    assert foo.r[0] == 1
    
    foo = Foo()
    with event.loop:
        foo.emit('foo', {})
        foo.emit('foo', {})
    assert len(foo.r) == 1
    assert foo.r[0] == 2


def test_integrate():
    
    res = []
    def calllater(f):
        res.append(f)
    
    ori = event.loop._calllaterfunc
    
    foo = Foo()
    event.loop.integrate(calllater)
    foo.emit('foo', {})
    foo.emit('foo', {})
    assert len(res) == 1 and res[0].__name__ == 'iter'
    
    with raises(ValueError):
        event.loop.integrate('not a callable')
    
    event.loop._calllaterfunc = ori


run_tests_if_main()
