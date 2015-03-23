""" Tests for Py to JS compilation
"""

from zoof.util.testing import run_tests_if_main
from zoof.ui.compile import js, py2js


@js
def t_func1():
    return 2 + 3

    
class TestClass:
    @js
    def method1(self, bar, spam=4, *more):
        pass
    
    def test_t_func1(self):
        code = t_func1.js.jscode
        line1 = code.split('\n')[0]
        assert 't_func1 = function' in line1
        assert 'function ()' in line1  # no args
    
    def test_ops(self):
        assert py2js('2+3') == '2 + 3;'
    
    def test_assignments(self):
        assert py2js('foo = 3') == 'var foo = 3;'
        assert py2js('foo.bar = 3') == 'foo.bar = 3;'


run_tests_if_main()


if __name__ == '__main__':
    t = TestClass()
    
    print(t_func1.js.jscode)