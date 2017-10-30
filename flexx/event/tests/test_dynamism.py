"""
Test reactions more wrt dynamism.
"""

import gc
import sys
import weakref

from flexx.util.testing import run_tests_if_main, skipif, skip, raises
from flexx.util.logging import capture_log

from flexx import event

loop = event.loop
logger = event.logger


class MyComponent(event.Component):
    
    a = event.AnyProp()
    aa = event.TupleProp()


def test_connectors1():
    """ test connectors """
    
    x = MyComponent()
    
    def foo(*events):
        pass
    
    # Can haz any char in label
    with capture_log('warning') as log:
        h = x.reaction(foo, 'a:+asdkjb&^*!')
    type = h.get_connection_info()[0][1][0]
    assert type.startswith('a:')
    assert not log
    
    # Warn if no known event
    with capture_log('warning') as log:
        h = x.reaction(foo, 'b')
    assert log
    x._Component__handlers.pop('b')
    
    # Supress warn
    with capture_log('warning') as log:
        h = x.reaction(foo, '!b')
    assert not log
    x._Component__handlers.pop('b')
    
    # Supress warn, with label
    with capture_log('warning') as log:
        h = x.reaction(foo, '!b:meh')
    assert not log
    x._Component__handlers.pop('b')
    
    # Supress warn, with label - not like this
    with capture_log('warning') as log:
        h = x.reaction(foo, 'b:meh!')
    assert log
    assert 'does not exist' in log[0]
    x._Component__handlers.pop('b')
    
    # Invalid syntax - but fix and warn
    with capture_log('warning') as log:
        h = x.reaction(foo, 'b!:meh')
    assert log
    assert 'Exclamation mark' in log[0]


def test_connectors2():
    """ test connectors with sub """
    
    x = MyComponent()
    y = MyComponent()
    x.sub = [y]
    
    def foo(*events):
        pass
    
    # Warn if no known event
    with capture_log('warning') as log:
        h = x.reaction(foo, 'sub*.b')
    assert log
    y._Component__handlers.pop('b')
    
    # Supress warn
    with capture_log('warning') as log:
        h = x.reaction(foo, '!sub*.b')
    assert not log
    y._Component__handlers.pop('b')
    
    # Supress warn, with label
    with capture_log('warning') as log:
        h = x.reaction(foo, '!sub*.b:meh')
    assert not log
    y._Component__handlers.pop('b')
    
    # Invalid syntax - but fix and warn
    with capture_log('warning') as log:
        h = x.reaction(foo, 'sub*.!b:meh')
    assert log
    assert 'Exclamation mark' in log[0]
    y._Component__handlers.pop('b')
    
    # Position of *
    with capture_log('warning') as log:
        h = x.reaction(foo, 'sub*.a')
    assert not log
    with capture_log('warning') as log:
        h = x.reaction(foo, 'sub.*.a')
    assert log
    with raises(ValueError):
        h = x.reaction(foo, 'sub.*a')  # fail

    # No star, no connection, fail!
    with raises(RuntimeError):
        h = x.reaction(foo, 'sub.b')
    
    # Mix it
    with capture_log('warning') as log:
        h = x.reaction(foo, '!aa*')
    assert not log
    with capture_log('warning') as log:
        h = x.reaction(foo, '!aa**')
    assert not log
    with capture_log('warning') as log:
        h = x.reaction(foo, '!aa**:meh')  # why not
    assert not log



def test_dynamism_and_handler_reconnecting():
    # Flexx' event system tries to be smart about reusing connections when
    # reconnections are made. This tests checks that this works, and when
    # it does not.

    class Foo(event.Component):
        def __init__(self):
            super().__init__()
        
        bars = event.ListProp(settable=True)
        
        def disconnect(self, *args):  # Detect disconnections
            super().disconnect(*args)
            disconnects.append(self)
    
    class Bar(event.Component):
        def __init__(self):
            super().__init__()
        
        spam = event.AnyProp(0, settable=True)
        
        def disconnect(self, *args):  # Detect disconnections
            super().disconnect(*args)
            disconnects.append(self)
    
    f = Foo()
    
    triggers = []
    disconnects = []
    
    @f.reaction('!bars*.spam')
    def handle_foo(*events):
        triggers.append(len(events))
    
    assert len(triggers) == 0
    assert len(disconnects) == 0
    
    # Assign new bar objects
    with event.loop:
        f.set_bars([Bar(), Bar()])
    #
    assert len(triggers) == 0
    assert len(disconnects) == 0
    
    # Change values of bar.spam
    with event.loop:
        f.bars[0].set_spam(7)
        f.bars[1].set_spam(42)
    #
    assert sum(triggers) == 2
    assert len(disconnects) == 0
    
    # Assign 3 new bar objects - old ones are disconnected
    with event.loop:
        f.set_bars([Bar(), Bar(), Bar()])
    #
    assert sum(triggers) == 2
    assert len(disconnects) == 2
    
    #
    
    # Append to bars property
    disconnects = []
    with event.loop:
        f.set_bars(f.bars + [Bar(), Bar()])
    assert len(disconnects) == 0
   
    # Append to bars property, drop one
    disconnects = []
    with event.loop:
        f.set_bars(f.bars[:-1] + [Bar(), Bar()])
    assert len(disconnects) == 1
    
    # Append to bars property, drop one at the wrong end: Flexx can't optimize
    disconnects = []
    with event.loop:
        f.set_bars(f.bars[1:] + [Bar(), Bar()])
    assert len(disconnects) == len(f.bars) - 1
    
    # Prepend to bars property
    disconnects = []
    with event.loop:
        f.set_bars([Bar(), Bar()] + f.bars)
    assert len(disconnects) == 0
    
    # Prepend to bars property, drop one
    disconnects = []
    with event.loop:
        f.set_bars([Bar(), Bar()] + f.bars[1:])
    assert len(disconnects) == 1
    
    # Prepend to bars property, drop one at the wrong end: Flexx can't optimize
    disconnects = []
    with event.loop:
        f.set_bars([Bar(), Bar()] + f.bars[:-1])
    assert len(disconnects) == len(f.bars) - 1


run_tests_if_main()
