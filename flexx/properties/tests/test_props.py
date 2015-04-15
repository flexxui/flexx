
from flexx.util.testing import run_tests_if_main

from flexx.properties import HasProps, Int, Float, Str


def test_basics():
    class MyClass(HasProps):
        i = Int()
        f = Float()
        s = Str()
    
    ob = MyClass()
    ob.i = 7
    assert ob.i == 7
    
# todo: definitely need more tests :P

run_tests_if_main()
