""" Tests signals and decorarors
"""

import sys

from pytest import raises
from flexx.util.testing import run_tests_if_main

from flexx.reactive import input, signal, react, source, UnboundError
from flexx.reactive import SourceSignal, InputSignal, Signal, ReactSignal

# todo: garbage collecting
# todo: HasSignals

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


## Signals


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
    
    @signal('s0')
    def s1(v):
        return v + 1
    
    @react('s1')  # <<< react!
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
    
    assert s1() is 10
    assert s3() is 12
    
    # Simulate ...
    s1(2)
    
    assert s1() is 2
    assert s2() is 3
    assert s3() is 4


def test_signal_last_value():
    
    @input
    def s0(v=10):
        return v
    
    @signal('s0')
    def s1(v):
        return v + 1
    
    assert s1.last_value is None
    s1()  # update
    assert s1.last_value is None
    
    s0(20)
    assert s1.last_value is None
    s1()
    assert s1.last_value == 11


def test_react_last_value():
    
    @input
    def s0(v=10):
        return v
    
    @react('s0')
    def s1(v):
        return v + 1
    
    assert s1.last_value is None
    
    s0(20)
    assert s1.last_value == 11


## Binding, unbound


def test_binding_unbound():
    
    @signal('nonexistent1')
    def s1(v):
        return v + 1
    
    assert isinstance(s1, Signal)
    assert s1.unbound
    raises(UnboundError, s1)
    raises(RuntimeError, s1.bind)
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


def test_unbinding():
    
    @input
    def s1(v=10):
        return float(v)
    
    @signal('s1')
    def s2(v):
        return v + 1
    
    assert not s2.unbound
    assert len(s2._upstream) == 1
    
    s2.unbind()
    
    assert s2.unbound
    assert len(s2._upstream) == 0
    
    
## Misc

def test_func_name():
    # Allow weird names, though not recommended
    # todo: do not allow this on hassignal classes.
    
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
        
        # creating a react signal binds it, invalidates it, updates it
        # -> error to stderr
        
        @react('s1')
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
        
        # creating a normal signal binds it, invalidates it. Stop
        # -> on calling, it should raise
        
        @signal('s1')
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
