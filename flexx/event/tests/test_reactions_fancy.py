"""
Test the more fancy stuff like:

* implicit reactions 
* computed properties
* setting properties as callables to create implicit actions
* more

"""

import gc
import sys
import weakref

from flexx.util.testing import run_tests_if_main, skipif, skip, raises
from flexx.event.both_tester import run_in_both, this_is_js
from flexx.util.logging import capture_log

from flexx import event

loop = event.loop
logger = event.logger



## Implici reactions


class MyObject1(event.Component):
    
    foo = event.IntProp(settable=True)
    bar = event.IntProp(7, settable=True)
    
    @event.reaction
    def report(self):
        print(self.foo, self.bar)


@run_in_both(MyObject1)
def test_reacion_implicit():
    """
    init
    False
    0 7
    4 7
    4 4
    end
    """
    
    print('init')
    m = MyObject1()
    print(m.report.is_explicit())
    loop.iter()
    
    # Invoke the reaction by modifying foo
    m.set_foo(3)
    m.set_foo(4)
    loop.iter()
    
    # Or bar
    m.set_bar(3)
    m.set_bar(24)
    m.set_bar(4)
    m.set_bar(4)
    loop.iter()
    
    # Modifying foo, but value does not change: no reaction
    m.set_foo(4)
    loop.iter()
    print('end')


class MyObject2(event.Component):
    
    bar = event.IntProp(7, settable=True)


@run_in_both(MyObject2)
def test_reaction_oneliner():
    """
    7
    2
    xx
    2
    3
    """
    
    m1 = MyObject2(bar=2)
    m2 = MyObject2(bar=lambda: m1.bar)
    loop.iter()
    print(m2.bar)
    loop.iter()
    print(m2.bar)
    
    print('xx')
    m1.set_bar(3)
    loop.iter()
    print(m2.bar)
    loop.iter()
    print(m2.bar)


run_tests_if_main()
