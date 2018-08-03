"""
Test reactions more wrt dynamism.
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


class Node(event.Component):

    val = event.IntProp(settable=True)
    parent = event.ComponentProp(settable=True)
    children = event.TupleProp(settable=True)

    @event.reaction('parent.val')
    def handle_parent_val(self, *events):
        xx = []
        for ev in events:
            if self.parent:
                xx.append(self.parent.val)
            else:
                xx.append(None)
        print('parent.val ' +  ', '.join([str(x) for x in xx]))

    @event.reaction('children*.val')
    def handle_children_val(self, *events):
        xx = []
        for ev in events:
            if isinstance(ev.new_value, (int, float)):
                xx.append(ev.new_value)
            else:
                xx.append(None)
        print('children.val ' + ', '.join([str(x) for x in xx]))


@run_in_both(Node)
def test_dynamism1():
    """
    parent.val 17
    parent.val 18
    parent.val 29
    done
    """

    n = Node()
    n1 = Node()
    n2 = Node()

    loop.iter()

    with loop:  # does not get trigger, because n1.val was not set
        n.set_parent(n1)
        n.set_val(42)
    with loop:
        n1.set_val(17)
        n2.set_val(27)
    with loop:
        n1.set_val(18)
        n2.set_val(28)
    with loop:  # does not trigger
        n.set_parent(n2)
    with loop:
        n1.set_val(19)
        n2.set_val(29)
    with loop:
        n.set_parent(None)
    with loop:
        n1.set_val(11)
        n2.set_val(21)

    print('done')


@run_in_both(Node)
def test_dynamism2a():
    """
    parent.val 17
    parent.val 18
    parent.val 29
    [17, 18, 29]
    """

    n = Node()
    n1 = Node()
    n2 = Node()

    res = []

    def func(*events):
        for ev in events:
            if n.parent:
                res.append(n.parent.val)
            else:
                res.append(None)
    n.reaction(func, 'parent.val')

    loop.iter()

    with loop:  # does not get trigger, because n1.val was not set
        n.set_parent(n1)
        n.set_val(42)
    with loop:
        n1.set_val(17)
        n2.set_val(27)
    with loop:
        n1.set_val(18)
        n2.set_val(28)
    with loop:  # does not trigger
        n.set_parent(n2)
    with loop:
        n1.set_val(19)
        n2.set_val(29)
    with loop:
        n.set_parent(None)
    with loop:
        n1.set_val(11)
        n2.set_val(21)

    print(res)


@run_in_both(Node)
def test_dynamism2b():
    """
    parent.val 17
    parent.val 18
    parent.val 29
    [None, None, 17, 18, None, 29, None]
    """
    n = Node()
    n1 = Node()
    n2 = Node()

    res = []

    def func(*events):
        for ev in events:
            if ev.type == 'val':
                res.append(n.parent.val)
            else:
                res.append(None)
    handler = n.reaction(func, 'parent', 'parent.val')  # also connect to parent

    loop.iter()

    with loop:  # does not get trigger, because n1.val was not set
        n.set_parent(n1)
        n.set_val(42)
    with loop:
        n1.set_val(17)
        n2.set_val(27)
    with loop:
        n1.set_val(18)
        n2.set_val(28)
    with loop:  # does not trigger
        n.set_parent(n2)
    with loop:
        n1.set_val(19)
        n2.set_val(29)
    with loop:
        n.set_parent(None)
    with loop:
        n1.set_val(11)
        n2.set_val(21)

    print(res)


@run_in_both(Node)
def test_dynamism3():
    """
    children.val 17, 27
    children.val 18, 28
    children.val 29
    done
    """

    n = Node()
    n1 = Node()
    n2 = Node()

    loop.iter()

    with loop:  # no trigger
        n.set_children((n1, n2))
        n.set_val(42)
    with loop:
        n1.set_val(17)
        n2.set_val(27)
    with loop:
        n1.set_val(18)
        n2.set_val(28)
    with loop:  # no trigger
        n.set_children((n2, ))
    with loop:
        n1.set_val(19)
        n2.set_val(29)
    with loop:
        n.set_children(())
    with loop:
        n1.set_val(11)
        n2.set_val(21)
    print('done')


@run_in_both(Node)
def test_dynamism4a():
    """
    children.val 17, 27
    children.val 18, 28
    children.val 29
    [17, 27, 18, 28, 29]
    """

    n = Node()
    n1 = Node()
    n2 = Node()

    res = []

    def func(*events):
        for ev in events:
            if isinstance(ev.new_value, (float, int)):
                res.append(ev.new_value)
            else:
                res.append(None)
    handler = n.reaction(func, 'children*.val')

    loop.iter()

    with loop:  # no trigger
        n.set_children((n1, n2))
        n.set_val(42)
    with loop:
        n1.set_val(17)
        n2.set_val(27)
    with loop:
        n1.set_val(18)
        n2.set_val(28)
    with loop:  # no trigger
        n.set_children((n2, ))
    with loop:
        n1.set_val(19)
        n2.set_val(29)
    with loop:
        n.set_children(())
    with loop:
        n1.set_val(11)
        n2.set_val(21)
    print(res)


@run_in_both(Node)
def test_dynamism4b():
    """
    children.val 17, 27
    children.val 18, 28
    children.val 29
    [None, None, 17, 27, 18, 28, None, 29, None]
    """

    n = Node()
    n1 = Node()
    n2 = Node()

    res = []

    def func(*events):
        for ev in events:
            if isinstance(ev.new_value, (float, int)):
                res.append(ev.new_value)
            else:
                res.append(None)
    handler = n.reaction(func, 'children', 'children*.val')  # also connect children

    loop.iter()

    with loop:  # no trigger
        n.set_children((n1, n2))
        n.set_val(42)
    with loop:
        n1.set_val(17)
        n2.set_val(27)
    with loop:
        n1.set_val(18)
        n2.set_val(28)
    with loop:  # no trigger
        n.set_children((n2, ))
    with loop:
        n1.set_val(19)
        n2.set_val(29)
    with loop:
        n.set_children(())
    with loop:
        n1.set_val(11)
        n2.set_val(21)
    print(res)


@run_in_both(Node)
def test_dynamism5a():
    """
    [0, 17, 18, 19]
    """

    # connection strings with static attributes - no reconnect
    n = Node()
    n1 = Node()
    n.foo = n1

    res = []
    def func(*events):
        for ev in events:
            if isinstance(ev.new_value, (float, int)):
                res.append(ev.new_value)
            else:
                res.append(None)

    # because the connection is fully resolved upon connecting, and at that time
    # the object is still in its init stage, the handler does get the init event
    # with value 0.
    handler = n.reaction(func, 'foo.val')
    loop.iter()

    with loop:
        n.set_val(42)
    with loop:
        n1.set_val(17)
        n1.set_val(18)
    with loop:
        n.foo = None  # no reconnect in this case
    with loop:
        n1.set_val(19)
    print(res)


@run_in_both(Node)
def test_dynamism5b():
    """
    [17, 18, 19]
    """

    # connection strings with static attributes - no reconnect
    n = Node()
    n1 = Node()
    n.foo = n1

    res = []
    def func(*events):
        for ev in events:
            if isinstance(ev.new_value, (float, int)):
                res.append(ev.new_value)
            else:
                res.append(None)

    # But not now
    loop.iter()  # <-- only change
    handler = n.reaction(func, 'foo.val')
    loop.iter()

    with loop:
        n.set_val(42)
    with loop:
        n1.set_val(17)
        n1.set_val(18)
    with loop:
        n.foo = None  # no reconnect in this case
    with loop:
        n1.set_val(19)
    print(res)




@run_in_both(Node)
def test_deep1():
    """
    children.val 7
    children.val 8
    children.val 17
    [7, 8, 17]
    """
    # deep connectors

    n = Node()
    n1 = Node()
    n2 = Node()
    n.set_children((Node(), n1))
    loop.iter()
    n.children[0].set_children((Node(), n2))
    loop.iter()

    res = []
    def func(*events):
        for ev in events:
            if isinstance(ev.new_value, (float, int)):
                if ev.new_value:
                    res.append(ev.new_value)
            else:
                res.append(None)
    handler = n.reaction(func, 'children**.val')

    loop.iter()

    # We want these
    with loop:
        n1.set_val(7)
    with loop:
        n2.set_val(8)
    # But not these
    with loop:
        n.set_val(42)
    with loop:
        n1.set_children((Node(), Node()))
        n.children[0].set_children([])
    # again ...
    with loop:
        n1.set_val(17)
    with loop:
        n2.set_val(18)  # n2 is no longer in the tree
    print(res)


@run_in_both(Node)
def test_deep2():
    """
    children.val 11
    children.val 12
    ['id12', 'id11', 'id10', 'id11']
    """
    # deep connectors - string ends in deep connector

    n = Node()
    n1 = Node()
    n2 = Node()
    n.set_children((Node(), n1))
    loop.iter()
    n.children[0].set_children((Node(), n2))
    loop.iter()

    res = []
    def func(*events):
        for ev in events:
            if isinstance(ev.new_value, (float, int)):
                res.append(ev.new_value)
            elif ev.type == 'children':
                if ev.source.val:
                    res.append('id%i' % ev.source.val)
            else:
                res.append(None)
    handler = n.reaction(func, 'children**')

    loop.iter()

    # Give val to id by - these should have no effect on res though
    with loop:
        n.set_val(10)
    with loop:
        n1.set_val(11)
    with loop:
        n2.set_val(12)
    # Change children
    with loop:
        n2.set_children((Node(), Node(), Node()))
        n1.set_children((Node(), Node()))
        n.set_children((Node(), n1, Node()))
    with loop:
        n2.set_children([])  # no longer in the tree
        n1.set_children([])
    print(res)



class TestOb(event.Component):

    children = event.TupleProp(settable=True)
    foo = event.StringProp(settable=True)


class Tester(event.Component):

    children = event.TupleProp(settable=True)

    @event.reaction('children**.foo')
    def track_deep(self, *events):
        for ev in events:
            if ev.new_value:
                print(ev.new_value)

    @event.action
    def set_foos(self, prefix):
        for i, child in enumerate(self.children):
            child.set_foo(prefix + str(i))
            for j, subchild in enumerate(child.children):
                subchild.set_foo(prefix + str(i) + str(j))

    @event.action
    def make_children1(self):
        t1 = TestOb()
        t2 = TestOb()
        t1.set_children((TestOb(), ))
        t2.set_children((TestOb(), ))
        self.set_children(t1, t2)

    @event.action
    def make_children2(self):
        for i, child in enumerate(self.children):
            child.set_children(child.children + (TestOb(), ))

    @event.action
    def make_children3(self):
        # See issue #460
        t = TestOb()
        my_children = self.children
        self.set_children(my_children + (t, ))
        for i, child in enumerate(my_children):
            child.set_children(child.children + (t, ))
        self.set_children(my_children)


@run_in_both(TestOb, Tester)
def test_issue_460_and_more():
    """
    A0
    A00
    A1
    A10
    -
    B0
    B00
    B01
    B1
    B10
    B11
    -
    C0
    C00
    C01
    C02
    C1
    C10
    C11
    C12
    """
    tester = Tester()
    loop.iter()

    tester.make_children1()
    loop.iter()

    tester.set_foos('A')
    loop.iter()

    print('-')

    tester.make_children2()
    loop.iter()

    tester.set_foos('B')
    loop.iter()

    print('-')

    tester.make_children3()
    loop.iter()

    tester.set_foos('C')
    loop.iter()


## Python only

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

    # y.a is not a list, fail!
    with raises(RuntimeError):
        h = y.reaction(foo, 'a*.b')

    # Mix it
    with capture_log('warning') as log:
        h = x.reaction(foo, '!aa**')
    with capture_log('warning') as log:
        h = x.reaction(foo, '!aa*')
    assert not log
    with capture_log('warning') as log:
        h = y.reaction(foo, '!aa*')
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
