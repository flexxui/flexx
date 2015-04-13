""" Tests for Py to JS compilation
"""

from pytest import raises
from flexx.util.testing import run_tests_if_main

from flexx.pyscript import js, JSError, py2js, evaljs, evalpy
from flexx import pyscript


def nowhitespace(s):
    return s.replace('\n', '').replace('\t', '').replace(' ', '')


class TestExpressions:
    """ Tests for single-line statements/expressions
    """
    
    def test_special(self):
        assert py2js('') == ''
        assert py2js('  \n') == ''
    
    def test_ops(self):
        # Test code
        assert py2js('2+3') == '2 + 3;'  # Binary
        assert py2js('2/3') == '2 / 3;'
        assert py2js('not 2') == '!2;'  # Unary
        assert py2js('-(2+3)') == '-(2 + 3);'
        assert py2js('True and False') == 'true && false;'  # Boolean
        assert py2js('4 > 3') == '4 > 3;'  # Comparisons
        assert py2js('4 is 3') == '4 === 3;'
        
        # No parentices around names, numbers and strings
        assert py2js('foo + bar') == "foo + bar;"
        assert py2js('_foo3 + _bar4') == "_foo3 + _bar4;"
        assert py2js('3 + 4') == "3 + 4;"
        assert py2js('"abc" + "def"') == "'abc' + 'def';"
        assert py2js("'abc' + 'def'") == "'abc' + 'def';"
        assert py2js("'abc' + \"'def\"") == "'abc' + \"'def\";"
        
        # But they should be if it gets more complex
        assert py2js('foo + bar == 3') == "(foo + bar) == 3;"
        
        # Test outcome
        assert evalpy('2+3') == '5'  # Binary
        assert evalpy('6/3') == '2'
        assert evalpy('4//3') == '1'
        assert evalpy('2**8') == '256'
        assert evalpy('not True') == 'false'  # Unary
        assert evalpy('- 3') == '-3'
        assert evalpy('True and False') == 'false'  # Boolean
        assert evalpy('True or False') == 'true'
    
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
        
        # Indexing
        assert evalpy('a=[0,0]\na[0]=2\na[1]=3\na', False) == '[2,3]'
    
    def test_aug_assignments(self):
        # assign + bin op
        assert evalpy('x=5; x+=1; x') == '6'
        assert evalpy('x=5; x/=2; x') == '2.5'
        assert evalpy('x=5; x**=2; x') == '25'
        assert evalpy('x=5; x//=2; x') == '2'
    
    def test_basic_types(self):
        assert py2js('True') == 'true;'
        assert py2js('False') == 'false;'
        assert py2js('None') == 'null;'
        
        assert py2js('"bla\\"bla"') == "'bla\"bla';"
        assert py2js('3') == '3;'
        assert py2js('3.1415') == '3.1415;'
        
        assert py2js('[1,2,3]') == '[1, 2, 3];'
        assert py2js('{foo: 3, bar: 4}') == '{foo: 3, bar: 4};'

    
    def test_ignore_import_of_compiler(self):
        modname = pyscript.__name__
        assert py2js('from %s import x, y, z\n42' % modname) == '42;'


class TestConrolFlow:
    
    def test_ignore_if_name_is_main(self):
        assert py2js('if __name__ == "__main__":4') == ''
        
    def test_if(self):
        # Normal if
        assert evalpy('if True: 4\nelse: 5') == '4'
        assert evalpy('if False: 4\nelse: 5') == '5'
        assert evalpy('x=4\nif x>3: 13\nelif x > 2: 12\nelse: 10') == '13'
        assert evalpy('x=3\nif x>3: 13\nelif x > 2: 12\nelse: 10') == '12'
        assert evalpy('x=1\nif x>3: 13\nelif x > 2: 12\nelse: 10') == '10'
        
        # One-line if
        line = py2js('3 if True else 4').replace(')', '').replace('(', '')
        assert line == 'true? 3 : 4;'
        #
        assert evalpy('4 if True else 5') == '4'
        assert evalpy('4 if False else 5') == '5'
        assert evalpy('3+1 if 0+2/1 else 4+1') == '4'
        assert evalpy('3+1 if 4/2-2 else 4+1') == '5'
    
    def test_for(self):
        
        # Test all possible ranges
        line = nowhitespace(py2js('for i in range(9): pass'))
        assert line == 'vari;for(i=0;i<9;i+=1){}'
        line = nowhitespace(py2js('for i in range(2, 99): pass'))
        assert line == 'vari;for(i=2;i<99;i+=1){}'
        line = nowhitespace(py2js('for i in range(100, 0, -1): pass'))
        assert line == 'vari;for(i=100;i>0;i+=-1){}'
        
        # Test enumeration (code)
        assert ' in ' not in py2js('for i in [1, 2, 3]: pass')
        assert ' in ' not in py2js('for i in {1:2, 2:3}: pass')
        
        # Test declaration of iteration variable
        assert 'var i;' in py2js('for i in x: pass')
        assert 'var i' in py2js('i=""\nfor i in x: pass')
        assert 'var i' not in py2js('j=i=""\nfor i in x: pass')
        
        # Test output for range
        assert evalpy('for i in range(3):\n  print(i)') == '0\n1\n2'
        assert evalpy('for i in range(1,6,2):\n  print(i)') == '1\n3\n5'
        
        # Test explicit for-array iteration
        code = py2js('a=[7,8]\nfor i in range(len(a)):\n  print(a[i])')
        assert ' in ' not in code and evaljs(code) == '7\n8'
        # Test enumeration over arrays - should use actual for-loop
        code = py2js('for k in [7, 8]:\n  print(k)')
        assert ' in ' not in code and evaljs(code) == '7\n8'
        
        # Test enumeration over dicts 
        # Python cannot see its a dict, and uses a for-loop
        code = py2js('d = {3:7, 4:8}\nfor k in d:\n  print(k)')
        assert ' in ' not in code and evaljs(code) == '3\n4'
        code = py2js('d = {3:7, 4:8}\nfor k in d:\n  print(d[k])')
        assert ' in ' not in code and evaljs(code) == '7\n8'
        # .keys()
        code = py2js('d = {3:7, 4:8}\nfor k in d.keys():\n  print(d[k])')
        assert ' in ' in code and evaljs(code) == '7\n8'
        # .values()
        code = py2js('d = {3:7, 4:8}\nfor v in d.values():\n  print(v)')
        assert ' in ' in code and evaljs(code) == '7\n8'
        # .items()
        code = py2js('d = {3:7, 4:8}\nfor k,v in d.items():\n  print(k)')
        assert ' in ' in code and evaljs(code) == '3\n4'
        code = py2js('d = {3:7, 4:8}\nfor k,v in d.items():\n  print(v)')
        assert ' in ' in code and evaljs(code) == '7\n8'
        
        # Test iterate over strings
        code = py2js('for c in "foo":\n  print(c)')
        assert evaljs(code) == 'f\no\no'
        
        # Break and continue
        for9 = 'for i in range(9):\n  '
        assert evalpy(for9 + 'if i==4:break\n  print(i)') == '0\n1\n2\n3'
        assert evalpy(for9 + 'if i<5:continue\n  print(i)') == '5\n6\n7\n8'
        
        # Else
        assert evalpy(for9 + 'if i==3:break\nelse: print(99)\n0') == '0'
        assert evalpy(for9 + 'if i==30:break\nelse: print(99)\n0') == '99\n0'
        
        # Nested loops correct else
        code = self.method_for.js.jscode
        assert evaljs('var x=%sx()' % code) == 'ok\nok'
    
    @js
    def method_for(self):
        for i in range(5):
            for j in range(5):
                if j == 4:
                    break
            else:
                print('this should not show')
        else:
            print('ok')
        
        for i in range(5):
            if i == 1:
                break
            for j in range(5):
                pass
            else:
                print('ok')
        else:
            print('this should not show')
    
    
    def test_while(self):
        
        # Test code output
        line = nowhitespace(py2js('while(True): pass'))
        assert line == 'while(true){}'
        line = nowhitespace(py2js('while(not ok): pass'))
        assert line == 'while(!ok){}'
        
        # Test break and continue
        for9 = 'i=-1\nwhile(i<8):\n  i+=1\n  '
        assert evalpy(for9 + 'if i==4:break\n  print(i)\n0') == '0\n1\n2\n3\n0'
        assert evalpy(for9 + 'if i<6:continue\n  print(i)\n0') == '6\n7\n8\n0'
        # Test else
        assert evalpy(for9 + 'if i==3:break\nelse: print(99)\n0') == '0'
        assert evalpy(for9 + 'if i==30:break\nelse: print(99)\n0') == '99\n0'


@js
def func1():
    return 2 + 3


class TestFuctions:
    
    def test_func_calls(self):
        assert py2js('foo()') == 'foo();'
        assert py2js('foo(3, 4)') == 'foo(3, 4);'
        assert py2js('foo(3, 4+1)') == 'foo(3, 4 + 1);'
        assert py2js('foo(3, *args)')  # JS is complex, just test it compiles
        
        # Does not work
        raises(JSError, py2js, 'foo(x=1, y=2)')
        raises(JSError, py2js, 'foo(**kwargs)')
    
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
        assert '4' in code
        
        assert evaljs('x=' + code + 'x(2)') == '6'
        assert evaljs('x=' + code + 'x(2, 2)') == '4'
        assert evaljs('x=' + code + 'x(0, 0)') == '0'
    
    @js
    def method3(self, *args):
        return args
    
    def test_var_args3(self):
        code1 = 'var x = ' + self.method3.js.jscode
        lines = [line for line in code1.split('\n') if line]
        
        code2 = py2js('x(2, 3)')
        assert evaljs(code1 + code2, False) == '[2,3]'
        code2 = py2js('x()')
        assert evaljs(code1 + code2, False) == '[]'
        code2 = py2js('a=[2,3]\nx(*a)')
        assert evaljs(code1 + code2, False) == '[2,3]'
        code2 = py2js('a=[2,3]\nx(1,2,*a)')
        assert evaljs(code1 + code2, False) == '[1,2,2,3]'
    
    @js
    def method4(self, foo, *args):
        return args
    
    def test_var_args4(self):
        code1 = 'var x = ' + self.method4.js.jscode
        lines = [line for line in code1.split('\n') if line]
        
        code2 = py2js('x(0, 2, 3)')
        assert evaljs(code1 + code2, False) == '[2,3]'
        code2 = py2js('x(0)')
        assert evaljs(code1 + code2, False) == '[]'
        code2 = py2js('a=[0,2,3]\nx(*a)')
        assert evaljs(code1 + code2, False) == '[2,3]'
        code2 = py2js('a=[2,3]\nx(0,1,2,*a)')
        assert evaljs(code1 + code2, False) == '[1,2,2,3]'
    
    @js
    def method_this(self):
        return self.foo
    
    def test_self_becomes_this(self):
        code = self.method_this.js.jscode
        lines = [line.strip() for line in code.split('\n') if line]
        assert 'return this.foo;' in lines
    
    def test_lambda(self):
        assert evalpy('f=lambda x:x+1\nf(2)') == '3'
        assert evalpy('(lambda x:x+1)(2)') == '3'
        
    @js
    def method_scope(self):
        def foo(z):
            y = 2
            stub = False
            return x + y + z
        x = 1
        y = 0
        y = 1
        z = 1
        res = foo(3)
        stub = True
        return res + y  # should return 1+2+3+1 == 7
    
    def test_scope(self):
        code = 'var x = ' + self.method_scope.js.jscode
        assert code.count('var y') == 2
        assert code.count('var stub') == 2
        assert evaljs(code + 'x()') == '7'


run_tests_if_main()
