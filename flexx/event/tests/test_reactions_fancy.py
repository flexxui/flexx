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
from flexx.event._both_tester import run_in_both, this_is_js
from flexx.util.logging import capture_log

from flexx import event

loop = event.loop
logger = event.logger


class MyObject(event.Component):
    
    foo = event.IntProp(settable=True)
    bar = event.IntProp(7, settable=True)
    
    @event.reaction
    def report(self):
        print(self.foo, self.bar)


@run_in_both(MyObject)
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
    m = MyObject()
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


run_tests_if_main()
