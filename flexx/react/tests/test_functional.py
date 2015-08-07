from pytest import raises
from flexx.util.testing import run_tests_if_main

from flexx import react


def test_map():
    
    @react.input
    def number(n=0):
        return float(n)
    
    # One way
    @react.connect(react.map(lambda x: x+1, 'number'))
    def reg1(v):
        return v
    
    # Or another
    reg2 = react.map(lambda x: x+2, 'number')
    
    assert reg1() == 1
    assert reg2() == 2
    
    number(42)
    
    assert reg1() == 43
    assert reg2() == 44


def test_filter():
    
    registered = []
    
    @react.input
    def number(n=0):
        return float(n)
    
    @react.connect(react.filter(lambda x: x>0, 'number'))
    def reg1(v):
        registered.append(v)
    
    number(3)
    number(-1)
    number(-5)
    number(3)
    number(-2)
    number(4)
    
    assert registered == [3, 3, 4]


run_tests_if_main()
