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


def test_reduce1():
    
    registered = []
    
    @react.input
    def number(n=0):
        return float(n)
    
    @react.connect(react.reduce(lambda x, y: x+y, 'number'))
    def reg1(v):
        registered.append(v)
    
    number(1)
    number(2)
    number(2)
    number(3)
    
    assert registered == [0, 1, 3, 5, 8]


def test_reduce2():
    
    registered = []
    
    @react.input
    def number(n=0):
        return float(n)
    
    @react.connect(react.reduce(lambda x, y: x+y, 'number', 1))
    def reg1(v):
        registered.append(v)
    
    number(1)
    number(2)
    number(2)
    number(3)
    
    assert registered == [1, 2, 4, 6, 9]


def test_merge():
    
    registered = []
    
    @react.input
    def number1(n=0):
        return float(n)
    
    @react.input
    def number2(n=0):
        return float(n)
    
    @react.connect(react.merge('number1', 'number2'))
    def reg1(v):
        registered.append(v)
    
    number1(1)
    number2(2)
    number2(3)
    
    assert registered == [(0, 0), (1, 0), (1, 2), (1, 3)]


run_tests_if_main()
