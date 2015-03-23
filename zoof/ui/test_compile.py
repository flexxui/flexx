""" Tests for Py to JS compilation
"""

import subprocess

from zoof.util.testing import run_tests_if_main
from zoof.ui.compile import js, py2js


def evaljs(code):
    """ Evaluate code in node. Return last result as string.
    """
    res = subprocess.check_output(['node', '-p', '-e', code])
    res = res.decode().rstrip()
    if res.endswith('undefined'):
        res = res[:-9].rstrip()
    return res

def evalpy(code):
    """ Evaluate python code (after translating to js)
    """
    return evaljs(py2js(code))


@js
def func1():
    return 2 + 3

    
class TestClass:
    
    ## Tests for single-line statements/expressions
    
    def test_special(self):
        assert py2js('') == ''
        assert py2js('  \n') == ''
    
    def test_ops(self):
        # Test code
        assert py2js('2+3') == '2 + 3;'
        assert py2js('2/3') == '2 / 3;'
        
        # Test outcome
        assert evalpy('2+3') == '5'
        assert evalpy('6/3') == '2'
        assert evalpy('4//3') == '1'
        assert evalpy('2**8') == '256'
    
    def test_assignments(self):
        assert py2js('foo = 3') == 'var foo = 3;'  # with var
        assert py2js('foo.bar = 3') == 'foo.bar = 3;'  # without var
        
        code = py2js('foo = 3; bar = 4')  # define both
        assert code.count('var') == 2
        code = py2js('foo = 3; foo = 4')  # only define first time
        assert code.count('var') == 1
        
        code = py2js('foo = bar = 3')  # multiple assignment
        assert 'foo = bar = 3' in code
        assert 'var foo, bar' in code
        
        # self -> this
        assert py2js('self') == 'this;'
        assert py2js('self.foo') == 'this.foo;'
    
    def test_basic_types(self):
        assert py2js('True') == 'true;'
        assert py2js('False') == 'false;'
        assert py2js('None') == 'null;'
        
        assert py2js('"bla\\"bla"') == "'bla\"bla';"
        assert py2js('3') == '3;'
        assert py2js('3.1415') == '3.1415;'
        
        assert py2js('[1,2,3]') == '[1, 2, 3];'
        assert py2js('{foo: 3, bar: 4}') == '{foo: 3, bar: 4};'
    
    def test_func_calls(self):
        assert py2js('foo()') == 'foo();'
        assert py2js('foo(3, 4)') == 'foo(3, 4);'
        assert py2js('foo(3, 4+1)') == 'foo(3, 4 + 1);'
        assert py2js('foo(x=1, y=2)') == 'foo({x: 1, y: 2});'
        assert py2js('foo(3, 4, x=1, y=2)') == 'foo(3, 4, {x: 1, y: 2});'
    
    def test_builtins(self):
        assert py2js('max(3, 4)') == 'max(3, 4);'
    
    def test_print(self):
        assert py2js('print()') == 'console.log();'
        assert py2js('print(3)') == 'console.log(3);'
        
        assert evalpy('print(3)') == '3'
        assert evalpy('print(3); print(3)') == '3\n3'
        assert evalpy('print(); print(3)') == '\n3'  # Test \n
        assert evalpy('print("hello world")') == 'hello world'
        
        assert evalpy('print(3, "hello")') == '3 hello'
        assert evalpy('print(3+1, "hello", 3+1)') == '4 hello 4'
    
    
    ## Test functions
    
    def test_func1(self):
        code = func1.js.jscode
        lines = [line for line in code.split('\n') if line]
        
        assert len(lines) == 3  # only three lines
        assert lines[0] == 'function () {'  # no args
        assert lines[1].startswith('  ')  # indented
        assert lines[2] == '};'  # dedented
    
    @js
    def method1(self):
        return 2 + 3
    
    def test_method1(self):
        code = self.method1.js.jscode
        lines = [line for line in code.split('\n') if line]
        
        assert len(lines) == 3  # only three lines
        assert lines[0] == 'function () {'  # no args, no self/this
        assert lines[1].startswith('  ')  # indented
        assert lines[2] == '};'  # dedented 
    
    @js
    def method2(self, foo, bar=4):
        return foo + bar
    
    def test_default_args(self):
        code = self.method2.js.jscode
        lines = [line for line in code.split('\n') if line]
        
        assert lines[0] == 'function (foo, bar) {'
        assert 'bar = bar || 4' in code
        
        assert evaljs('x=' + code + 'x(2)') == '6'
        assert evaljs('x=' + code + 'x(2, 2)') == '4'
    
    @js
    def method3(self, *args):
        return args
    
    def test_var_args3(self):
        code = self.method3.js.jscode
        lines = [line for line in code.split('\n') if line]
        
        assert evaljs('x=' + code + 'x(2, 3)').replace(' ', '') == '[2,3]'
        assert evaljs('x=' + code + 'x()').replace(' ', '') == '[]'    
    
    @js
    def method4(self, foo, *args):
        return args
    
    def test_var_args4(self):
        code = self.method4.js.jscode
        lines = [line for line in code.split('\n') if line]
        
        assert evaljs('x=' + code + 'x(0, 2, 3)').replace(' ', '') == '[2,3]'
        assert evaljs('x=' + code + 'x(0)').replace(' ', '') == '[]' 
    
    ## Control flow
    
    def test_if1(self):
        assert evalpy('x=3\nif x<3: 4\nelse: 5') == 5

run_tests_if_main()


if __name__ == '__main__':
    t = TestClass()
    