""" Tests for reactive
"""

from pytest import raises
from flexx.util.testing import run_tests_if_main

from flexx.reactive import input, signal, react, UnboundError
from flexx.reactive import InputSignal, Signal, ReactSignal


def test_input_simple():
    
    @input
    def tester(v=10):
        if v < 0:
            raise ValueError()
        return v + 2
    
    assert isinstance(tester, Signal)
    assert isinstance(tester, InputSignal)
    
    assert tester() == 12
    assert '12' in repr(tester)

    tester(20)
    assert tester() == 22
    assert '22' in repr(tester)
    
    raises(ValueError, tester, -1)
    assert tester() == 22  # old value maintained


def test_input_no_default():
    
    @input
    def tester(v):
        if v < 0:
            raise ValueError()
        return v + 2
    
    assert tester() is None
    
    # Maintain None after failed set
    raises(ValueError, tester, -1)
    assert tester() is None
    
    tester(20)
    assert tester() == 22
    
    raises(ValueError, tester, -1)
    assert tester() == 22  # old value maintained


def test_input_with_upstream():
    
    @input
    def s1(v=10):
        return float(v)
    
    @input('s1')
    def s2(v2=20, v1=None):
        if v1 is None:
            return float(v2)
        else:
            return v1 + 5
    
    assert s1() == 10
    assert s2() == 20
    
    s1(100)
    assert s1() == 100
    assert s2() == 105
    
    s2(200)
    assert s1() == 100
    assert s2() == 200


def test_input_circular():
    
    @input('s2')
    def s1(v1=15, v2=None):
        if v2 is None:
            return float(v1)
        else:
            return v2 - 5
    
    @input('s1')
    def s2(v2=20, v1=None):
        if v1 is None:
            return float(v2)
        else:
            return v1 + 5
    
    s1.bind()
    
    assert s1() == 15
    assert s2() == 20
    
    s1(100)
    assert s1() == 100
    assert s2() == 105
    
    s2(200)
    assert s1() == 195
    assert s2() == 200


## ---------------------


def test_signal_no_upstream():
    # Signals *must* have upstream signals
    
    with raises(ValueError):
        @signal
        def s1(v):
            return v + 1
    
    with raises(ValueError):
        @signal()
        def s1(v):
            return v + 1
    
    with raises(ValueError):
        @react
        def s1(v):
            return v + 1
    
    with raises(ValueError):
        @react()
        def s1(v):
            return v + 1


def test_signal_pull():
    
    s2_called = []
    
    @input
    def s0(v=10):
        return v
    
    @signal('s0')
    def s1(v):
        return v + 1
    
    @signal('s1')
    def s2(v):
        s2_called.append(v)
        return v + 2
    
    assert len(s2_called) == 1
    assert s2() == 13
    assert s1() == 11
    
    s0(20)
    assert len(s2_called) == 1  # lazy evaluation
    assert s2() == 23
    assert len(s2_called) == 2
    

def test_signal_push():
    
    s2_called = []
    
    @input
    def s0(v=10):
        return v
    
    @signal('s0')
    def s1(v):
        return v + 1
    
    @react('s1')  # <<< react!
    def s2(v):
        s2_called.append(v)
        return v + 2
    
    assert len(s2_called) == 1
    assert s2() == 13
    assert s1() == 11
    
    s0(20)
    assert len(s2_called) == 2  # react directly
    assert s2() == 23
    assert len(s2_called) == 2


def test_signal_circular():
    
    @signal('s3')
    def s1(v):
        return v + 1
    
    @signal('s1')
    def s2(v):
        return v + 1
    
    @signal('s2')
    def s3(v):
        return v + 1
    
    s1.bind()
    
    assert not s1.unbound
    assert not s2.unbound
    assert not s2.unbound
    
    # The fact that we have no recursion-limit-reached here is part of the test
    
    assert s1() is None
    assert s3() is None
    
    # Simulate ...
    s1._value = 2
    s2._set_dirty(s1)
    
    assert s1() is 2
    assert s2() is 3
    assert s3() is 4


## ---------------------------


def test_binding_unbound():
    
    @signal('nonexistent1')
    def s1(v):
        return v + 1
    
    assert isinstance(s1, Signal)
    assert s1.unbound
    raises(UnboundError, s1)
    assert 'unbound' in repr(s1).lower()
    
    # todo: what if upstream is unbound?


def test_binding_signal():
    
    @signal('s1')
    def s2(v):
        return v + 1
    
    assert s2.unbound
    
    @input
    def s1(v=10):
        return float(v)
    
    assert s2.unbound
    assert 'unbound' in repr(s2)
    assert s2.unbound
    
    s1(20)
    assert s2.unbound
    
    # Calling a signal tries to bind it if its unbound
    assert s2() == 21


def test_binding_react():
    
    reacted = []
    
    @react('s1')
    def s2(v):
        reacted.append(v)
    
    assert s2.unbound
    
    @input
    def s1(v=10):
        return float(v)
    
    assert s2.unbound
    assert 'unbound' in repr(s2)
    assert s2.unbound
    
    s1(20)
    assert s2.unbound
    assert len(reacted) == 0
    
    # Calling a signal tries to bind it if its unbound
    s2()
    assert len(reacted) == 1 and reacted[0] == 20


run_tests_if_main()
