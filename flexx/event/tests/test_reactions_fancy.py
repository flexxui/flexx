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



## Greedy reactions

class MyObject1(event.Component):

    foo = event.IntProp(settable=True)
    bar = event.IntProp(settable=True)

    @event.reaction('foo')
    def report1(self, *events):
        print('foo', self.foo)

    @event.reaction('bar', mode='greedy')
    def report2(self, *events):
        print('bar', self.bar)


@run_in_both(MyObject1)
def test_reaction_greedy():
    """
    normal greedy
    bar 0
    foo 0
    -
    foo 4
    -
    bar 4
    -
    foo 6
    bar 6
    foo 6
    """

    m = MyObject1()
    print(m.report1.get_mode(), m.report2.get_mode())
    loop.iter()
    print('-')

    # Invoke the reaction by modifying foo
    m.set_foo(3)
    m.set_foo(4)
    loop.iter()
    print('-')

    # Or bar
    m.set_bar(3)
    m.set_bar(4)
    loop.iter()
    print('-')

    # But now interleave
    m.set_foo(4)
    m.set_bar(4)
    m.set_foo(5)
    m.set_bar(5)
    m.set_foo(6)
    m.set_bar(6)
    loop.iter()


## Automatic reactions


class MyObject2(event.Component):

    foo = event.IntProp(settable=True)
    bar = event.IntProp(7, settable=True)

    @event.reaction
    def report(self, *events):
        assert len(events) == 0  # of course, you'd leave them out in practice
        print(self.foo, self.bar)


@run_in_both(MyObject2)
def test_reaction_auto1():
    """
    init
    auto
    0 7
    4 7
    4 4
    end
    """

    print('init')
    m = MyObject2()
    print(m.report.get_mode())
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


class MyObject3(event.Component):

    foo = event.IntProp(settable=True)
    bar = event.IntProp(7, settable=True)

    @event.reaction('!spam', mode='auto')
    def report(self, *events):
        assert len(events) > 0
        print(self.foo, self.bar)


@run_in_both(MyObject3)
def test_reaction_auto2():
    """
    init
    auto
    0 7
    4 7
    4 4
    4 4
    end
    """

    print('init')
    m = MyObject3()
    print(m.report.get_mode())
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

    m.emit('spam')
    loop.iter()

    # Modifying foo, but value does not change: no reaction
    m.set_foo(4)
    loop.iter()
    print('end')


## One liner

class MyObject4(event.Component):

    bar = event.IntProp(7, settable=True)


@run_in_both(MyObject4)
def test_reaction_oneliner():
    """
    7
    2
    xx
    2
    3
    """

    m1 = MyObject4(bar=2)
    m2 = MyObject4(bar=lambda: m1.bar)
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
