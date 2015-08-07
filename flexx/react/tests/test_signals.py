""" Tests signals and decorarors
"""

import sys

from pytest import raises
from flexx.util.testing import run_tests_if_main

from flexx import react
from flexx.react import connect, input, source, lazy, SignalValueError, undefined
from flexx.react import Signal, SourceSignal, InputSignal, LazySignal

# todo: garbage collecting
# todo: HasSignals

## Misc


def test_object_frame():
    class X:
        def __init__(self):
            self.foo = 42
    ob = X()
    frame = sys._getframe(0)
    f = react.signals.ObjectFrame(ob, frame)
    assert f.f_locals['foo'] == 42
    assert f.f_globals is frame.f_globals
    assert f.f_back.f_locals['foo'] == 42


## Inputs


def test_source_simple():
    # For the rest we only test input signals
    
    @source
    def tester(v=10):
        return v
    
    assert isinstance(tester, Signal)
    assert isinstance(tester, SourceSignal)
    
    assert tester() == 10
    assert '10' in repr(tester)

    tester._set(20)
    assert tester() == 20
    assert '20' in repr(tester)


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
    
    raises(ValueError, tester, 1, 2)   # multiple args

def test_input_no_default():
    
    @input
    def tester(v):
        if v < 0:
            raise ValueError()
        return v + 2
    
    raises(SignalValueError, tester)
    
    # Maintain None after failed set
    raises(ValueError, tester, -1)
    raises(SignalValueError, tester)
    
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
    
    s1.connect()
    s2.connect()
    
    assert s1() == 15
    assert s2() == 20
    
    s1(100)
    assert s1() == 100
    assert s2() == 105
    
    s2(200)
    assert s1() == 195
    assert s2() == 200


## Normal and Lazy


def test_signals_no_upstream():
    # Normal signals and lazy signals *must* have upstream signals
    
    with raises(ValueError):
        @lazy
        def s1(v):
            return v + 1
    
    with raises(ValueError):
        @lazy()
        def s1(v):
            return v + 1
    
    with raises(ValueError):
        @connect
        def s1(v):
            return v + 1
    
    with raises(ValueError):
        @connect()
        def s1(v):
            return v + 1


def test_signal_pull():
    
    s2_called = []
    
    @input
    def s0(v=10):
        return v
    
    @lazy('s0')
    def s1(v):
        return v + 1
    
    @lazy('s1')
    def s2(v):
        s2_called.append(v)
        return v + 2
    
    assert len(s2_called) == 0  # pull!
    assert s2() == 13
    assert s2() == 13
    assert s2() == 13
    assert s1() == 11
    assert len(s2_called) == 1  # called 3x, updated 1x
    
    s0(20)
    assert len(s2_called) == 1  # lazy evaluation
    assert s2() == 23
    assert len(s2_called) == 2
    

def test_signal_push():
    
    s2_called = []
    
    @input
    def s0(v=10):
        return v
    
    @lazy('s0')
    def s1(v):
        return v + 1
    
    @connect('s1')  # <<< react!
    def s2(v):
        s2_called.append(v)
        return v + 2
    
    assert len(s2_called) == 1  # updated directly
    assert s2() == 13
    assert s2() == 13
    assert s2() == 13
    assert s1() == 11
    assert len(s2_called) == 1  # called 3x, updated 1x
    
    s0(20)
    assert len(s2_called) == 2  # react directly
    assert s2() == 23
    assert len(s2_called) == 2


def test_signal_circular():
    
    @input('s3')
    def s1(v1=10, v3=None):
        if v3 is None:
            return v1
        else:
            return v3 + 1
    
    @lazy('s1')
    def s2(v):
        return v + 1
    
    @lazy('s2')
    def s3(v):
        return v + 1
    
    s1.connect()
    
    assert not s1.not_connected
    assert not s2.not_connected
    assert not s2.not_connected
    
    # The fact that we have no recursion-limit-reached here is part of the test
    
    assert s1() is 10
    assert s3() is 12
    
    # Simulate ...
    s1(2)
    
    assert s1() is 2
    assert s2() is 3
    assert s3() is 4


def test_lazy_last_value():
    
    @input
    def s0(v=10):
        return v
    
    @lazy('s0')
    def s1(v):
        return v + 1
    
    assert s1.last_value is undefined
    s1()  # update
    assert s1.last_value is undefined
    
    s0(20)
    assert s1.last_value is undefined
    s1()
    assert s1.last_value == 11


def test_normal_last_value():
    
    @input
    def s0(v=10):
        return v
    
    @connect('s0')
    def s1(v):
        return v + 1
    
    assert s1.last_value is undefined
    
    s0(20)
    assert s1.last_value == 11


## Connecting


def test_connecting_disconnected():
    
    @connect('nonexistent1')
    def s1(v):
        return v + 1
    
    assert isinstance(s1, Signal)
    assert s1.not_connected
    raises(SignalValueError, s1)
    raises(RuntimeError, s1.connect)
    assert 'not connected' in repr(s1).lower()
    
    # todo: what if upstream is not connected?


def test_connecting_signal():
    
    @connect('s1')
    def s2(v):
        return v + 1
    
    assert s2.not_connected
    
    @input
    def s1(v=10):
        return float(v)
    
    assert s2.not_connected
    assert 'not connected' in repr(s2)
    assert s2.not_connected
    
    s1(20)
    assert s2.not_connected
    
    # Calling a signal tries to connect it if its not connected
    assert s2() == 21


def test_connecting_react():
    
    reacted = []
    
    @connect('s1')
    def s2(v):
        reacted.append(v)
    
    assert s2.not_connected
    
    @input
    def s1(v=10):
        return float(v)
    
    assert s2.not_connected
    assert 'not connected' in repr(s2)
    assert s2.not_connected
    
    s1(20)
    assert s2.not_connected
    assert len(reacted) == 0
    
    # Calling a signal tries to connect it if its not connected
    s2()
    assert len(reacted) == 1 and reacted[0] == 20


def test_disconnecting():
    
    @input
    def s1(v=10):
        return float(v)
    
    @connect('s1')
    def s2(v):
        return v + 1
    
    assert not s2.not_connected
    assert len(s2._upstream) == 1
    
    s2.disconnect()
    
    assert s2.not_connected
    assert len(s2._upstream) == 0
    
    # Autoconnect
    s2()
    assert not s2.not_connected


## Misc

def test_func_name():
    # Allow weird names, though not recommended
    
    s = Signal(lambda x: x, [])
    assert 'lambda' in s.name
    
    s = Signal(float, [])
    assert s.name == 'float'


def test_errors():
    
    # Capture stderr
    errors = []
    def _fake_err(msg):
        errors.append(msg)
    old_error = sys.stderr.write
    sys.stderr.write = _fake_err
    
    try:
        reacted = []
        
        @input
        def s1(v=10):
            return float(v)
        
        # creating a react signal connects it, invalidates it, updates it
        # -> error to stderr
        
        @connect('s1')
        def s2(v):
            reacted.append(v)
            1/0
        
        assert len(reacted) == 1
        # hooray, we got here safely, but there should be printing to stderr
        assert 'ZeroDivision' in ''.join(errors)
        
        # Updating s1 should invoke the same ...
        errors[:] = []
        s1(20)
        assert len(reacted) == 2
        assert 'ZeroDivision' in ''.join(errors)
        
        # creating a lazy signal connects it, invalidates it. Stop
        # -> on calling, it should raise
        
        @lazy('s1')
        def s3(v):
            reacted.append(v)
            1/0
        
        assert len(reacted) == 2
        raises(ZeroDivisionError, s3)
        assert len(reacted) == 3
        
        # Calling it again ... raises again
        raises(ZeroDivisionError, s3)
        assert len(reacted) == 4
    
    finally:
        sys.stderr.write = old_error  # Set back


run_tests_if_main()
