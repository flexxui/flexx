""" Tests for Py to JS compilation
"""

from pytest import raises
from flexx.util.testing import run_tests_if_main

from flexx.pyscript import js, JSError, py2js, evaljs, evalpy, BaseParser
from flexx import pyscript


def nowhitespace(s):
    return s.replace('\n', '').replace('\t', '').replace(' ', '')


class TestParser(BaseParser):
    
    def function_foo_foo(self, node):
        return 'xxx'
    
    def method_bar_bar(self, node, base):
        return base


class TestTheBaseParser:
    
    def test_special_functions(self):
        assert TestParser("foo_foo()").dump() == 'xxx;'
        assert TestParser("bar_bar()").dump() == 'bar_bar();'
        
        assert TestParser("xxx.bar_bar()").dump() == 'xxx;'
        assert TestParser("xxx.foo_foo()").dump() == 'xxx.foo_foo();'


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
    
    def test_indexing_and_slicing(self):
        c = 'a = [1, 2, 3, 4, 5]\n'
        
        # Indexing
        assert evalpy(c + 'a[2]') == '3'
        assert evalpy(c + 'a[-2]') == '4'
        
        # Slicing
        assert evalpy(c + 'a[:]') == '[ 1, 2, 3, 4, 5 ]'
        assert evalpy(c + 'a[1:-1]') == '[ 2, 3, 4 ]'
    
    def test_assignments(self):
        assert py2js('foo = 3') == 'var foo;\nfoo = 3;'  # with var
        assert py2js('foo.bar = 3') == 'foo.bar = 3;'  # without var
        
        code = py2js('foo = 3; bar = 4')  # define both
        assert code.count('var') == 1
        code = py2js('foo = 3; foo = 4')  # only define first time
        assert code.count('var') == 1
        
        code = py2js('foo = bar = 3')  # multiple assignment
        assert 'foo = bar = 3' in code
        assert 'var bar, foo' in code  # alphabetic order
        
        # self -> this
        assert py2js('self') == 'this;'
        assert py2js('self.foo') == 'this.foo;'
        
        # Indexing
        assert evalpy('a=[0,0]\na[0]=2\na[1]=3\na', False) == '[2,3]'
        
        # Tuple unpacking
        evalpy('x=[1,2,3]\na, b, c = x\nb', False) == '2'
        evalpy('a,b,c = [1,2,3]\nc,b,a = a,b,c\n[a,b,c]', False) == '[3,2,1]'
    
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
        assert py2js('(1,2,3)') == '[1, 2, 3];'
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
        assert 'var aa' in py2js('for aa in x: pass')
        assert 'var aa' in py2js('aa=""\nfor aa in x: pass')
        assert 'var aa' in py2js('j=aa=""\nfor aa in x: pass')
        
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
        code = self.method_for.jscode
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


class TestExceptions:
    
    def test_raise(self):
        
        assert 'throw' in py2js('raise MyException("foo")')
        assert 'MyException' in py2js('raise MyException("foo")')
        assert 'foo' in py2js('raise MyException("foo")')
        
        # todo: we cannot eval-test this while we have no catch
    
    def test_assert(self):
        
        assert 'throw' in py2js('assert True')
        evalpy('assert true; 7') == '7'
        evalpy('assert true, "msg"; 7') == '7'


@js
def func1():
    return 2 + 3


class TestFuctions:
    
    def test_func_calls(self):
        assert py2js('foo()') == 'foo();'
        assert py2js('foo(3, 4)') == 'foo(3, 4);'
        assert py2js('foo(3, 4+1)') == 'foo(3, 4 + 1);'
        assert py2js('foo(3, *args)')  # JS is complex, just test it compiles
        assert py2js('a.foo(3, *args)')  # JS is complex, just test it compiles
        
        # Does not work
        raises(JSError, py2js, 'foo(x=1, y=2)')
        raises(JSError, py2js, 'foo(**kwargs)')
        
        code = "def foo(x): return x + 1\nd = {'foo':foo}\n"
        assert evalpy(code + 'foo(3)') == '4'
        assert evalpy(code + 'd.foo(3)') == '4'
        
        code = "def foo(x, *xx): return x + sum(xx)\nd = {'foo':foo}\nfive=[2, 3]\n"
        assert evalpy(code + 'foo(1, 2, 3)') == '6'
        assert evalpy(code + 'd.foo(1, 2, 3)') == '6'
        #
        assert evalpy(code + 'foo(1, *five)') == '6'
        assert evalpy(code + 'd.foo(1, *five)') == '6'
    
    
    def test_func1(self):
        code = func1.jscode
        lines = [line for line in code.split('\n') if line]
        
        assert len(lines) == 3  # only three lines
        assert lines[0] == 'function () {'  # no args
        assert lines[1].startswith('  ')  # indented
        assert lines[2] == '};'  # dedented
    
    @js
    def method1(self):
        return
    
    def test_method1(self):
        code = self.method1.jscode
        lines = [line for line in code.split('\n') if line]
        
        assert len(lines) == 3  # only three lines
        assert lines[0] == 'function () {'  # no args, no self/this
        assert lines[1].startswith('  ')  # indented
        assert lines[2] == '};'  # dedented 
    
    def test_default_args(self):
        
        @js
        def func(self, foo, bar=4):
            return foo + bar
        
        code = func.jscode
        lines = [line for line in code.split('\n') if line]
        
        assert lines[0] == 'function (foo, bar) {'
        assert '4' in code
        
        assert evaljs('x=' + code + 'x(2)') == '6'
        assert evaljs('x=' + code + 'x(2, 2)') == '4'
        assert evaljs('x=' + code + 'x(0, 0)') == '0'
    
    def test_var_args1(self):
        
        @js
        def func(self, *args):
            return args
        
        code1 = 'var x = ' + func.jscode
        lines = [line for line in code1.split('\n') if line]
        
        code2 = py2js('x(2, 3)')
        assert evaljs(code1 + code2, False) == '[2,3]'
        code2 = py2js('x()')
        assert evaljs(code1 + code2, False) == '[]'
        code2 = py2js('a=[2,3]\nx(*a)')
        assert evaljs(code1 + code2, False) == '[2,3]'
        code2 = py2js('a=[2,3]\nx(1,2,*a)')
        assert evaljs(code1 + code2, False) == '[1,2,2,3]'
    
    def test_var_args2(self):
        
        @js
        def func(self, foo, *args):
            return args
        
        code1 = 'var x = ' + func.jscode
        lines = [line for line in code1.split('\n') if line]
        
        code2 = py2js('x(0, 2, 3)')
        assert evaljs(code1 + code2, False) == '[2,3]'
        code2 = py2js('x(0)')
        assert evaljs(code1 + code2, False) == '[]'
        code2 = py2js('a=[0,2,3]\nx(*a)')
        assert evaljs(code1 + code2, False) == '[2,3]'
        code2 = py2js('a=[2,3]\nx(0,1,2,*a)')
        assert evaljs(code1 + code2, False) == '[1,2,2,3]'
    
    def test_self_becomes_this(self):
        @js
        def func(self):
            return self.foo
        
        code = func.jscode
        lines = [line.strip() for line in code.split('\n') if line]
        assert 'return this.foo;' in lines
    
    def test_lambda(self):
        assert evalpy('f=lambda x:x+1\nf(2)') == '3'
        assert evalpy('(lambda x:x+1)(2)') == '3'
    
    def test_scope(self):
        
        @js
        def func(self):
            def foo(z):
                y = 2
                stub = False
                only_here = 1
                return x + y + z
            x = 1
            y = 0
            y = 1
            z = 1
            res = foo(3)
            stub = True
            return res + y  # should return 1+2+3+1 == 7
        
        code = 'var x = ' + func.jscode
        vars1 = code.splitlines()[1]
        vars2 = code.splitlines()[3]
        assert vars1.strip().startswith('var ')
        assert vars2.strip().startswith('var ')
        
        assert 'y' in vars1 and 'y' in vars2
        assert 'stub' in vars1 and 'stub' in vars2
        assert 'only_here' in vars2 and 'only_here' not in vars1
        assert evaljs(code + 'x()') == '7'

    def test_raw_js(self):
        
        @js
        def func(a, b):
            """ 
            var c = 3;
            return a + b + c;
            """
        
        code = 'var x = ' + func.jscode
        assert evaljs(code + 'x(100, 10)') == '113'
        assert evaljs(code + 'x("x", 10)') == 'x103'
    
    def test_docstring(self):
        # And that its not interpreted as raw js
        
        @js
        def func(a, b):
            """ docstring """
            return a + b
        
        code = 'var x = ' + func.jscode
        assert evaljs(code + 'x(100, 10)') == '110'
        assert evaljs(code + 'x("x", 10)') == 'x10'
        
        assert code.count('// docstring') == 1


class TestClasses:
    
    
    def test_class(self):
        @js
        class MyClass:
            """ docstring """
            foo = 7
            foo = foo + 1
            
            def __init__(self):
                self.bar = 7
            def addOne(self):
                self.bar += 1
        
        code = MyClass.jscode + 'var m = new MyClass();'
        
        assert code.count('// docstring') == 1
        assert evaljs(code + 'm.bar;') == '7'
        assert evaljs(code + 'm.addOne();m.bar;') == '8'
            
        # class vars
        assert evaljs(code + 'm.foo;') == '8'
    
    
    def test_inheritance_and_super(self):
        
        class MyClass1:
            def __init__(self):
                self.bar = 7
            def add(self, x=1):
                self.bar += x
            def addTwo(self):
                self.bar += 2
        
        class MyClass2(MyClass1):
            def addTwo(self):
                super().addTwo()
                self.bar += 1  # haha, we add three!
        
        class MyClass3(MyClass2):
            def addTwo(self):
                super().addTwo()
                self.bar += 1  # haha, we add four!
            def addFour(self):
                super().add(4)
        
        code = js(MyClass1).jscode + js(MyClass2).jscode + js(MyClass3).jscode
        code += 'var m1=new MyClass1(), m2=new MyClass2(), m3=new MyClass3();'
        
        # m1
        assert evaljs(code + 'm1.bar;') == '7'
        assert evaljs(code + 'm1.add();m1.bar;') == '8'
        assert evaljs(code + 'm1.addTwo();m1.bar;') == '9'
        # m2
        assert evaljs(code + 'm2.bar;') == '7'
        assert evaljs(code + 'm2.add();m2.bar;') == '8'
        assert evaljs(code + 'm2.addTwo();m2.bar;') == '10'
        # m3
        assert evaljs(code + 'm3.bar;') == '7'
        assert evaljs(code + 'm3.add();m3.bar;') == '8'
        assert evaljs(code + 'm3.addTwo();m3.bar;') == '11'
        assert evaljs(code + 'm3.addFour();m3.bar;') == '11'  # super with args
        
        # Inhertance m1
        assert evaljs(code + 'm1 instanceof MyClass3;') == 'false'
        assert evaljs(code + 'm1 instanceof MyClass2;') == 'false'
        assert evaljs(code + 'm1 instanceof MyClass1;') == 'true'
        assert evaljs(code + 'm1 instanceof Object;') == 'true'
        
        # Inhertance m2
        assert evaljs(code + 'm2 instanceof MyClass3;') == 'false'
        assert evaljs(code + 'm2 instanceof MyClass2;') == 'true'
        assert evaljs(code + 'm2 instanceof MyClass1;') == 'true'
        assert evaljs(code + 'm2 instanceof Object;') == 'true'
        
        # Inhertance m3
        assert evaljs(code + 'm3 instanceof MyClass3;') == 'true'
        assert evaljs(code + 'm3 instanceof MyClass2;') == 'true'
        assert evaljs(code + 'm3 instanceof MyClass1;') == 'true'
        assert evaljs(code + 'm3 instanceof Object;') == 'true'


class TestModules:
    
    def test_module(self):
        
        code = BaseParser('"docstring"\nfoo=3;bar=4;_priv=0;', 'mymodule').dump()
        
        # Has docstring
        assert code.count('// docstring') == 1
        
        # Test that global variables exist
        assert evaljs(code+'mymodule.foo+mymodule.bar') == '7'
        
        # And privates do not
        assert evaljs(code+'mymodule._priv===undefined') == 'true'


run_tests_if_main()
# if __name__ == '__main__':
#     t = TestClasses()
#     t.test_class()
#     t.test_inheritance()

