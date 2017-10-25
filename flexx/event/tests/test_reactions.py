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
        print('r1 ' + str(len(events)))
    
    @event.reaction('!a', '!b')
    def r2(self, *events):
        print('r2 ' + str(len(events)))


@run_in_both(MyObject1)
def test_reaction_simple():
    """
    r1 1
    r2 2
    """
    m = MyObject1()
    
    with loop:
        m.emit('a', {})
        m.emit('b', {})


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
