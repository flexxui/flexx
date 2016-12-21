import sys

from flexx.util.testing import run_tests_if_main, raises, skipif

from flexx.pyscript import RawJS, JSError, py2js, evaljs, evalpy


def nowhitespace(s):
    return s.replace('\n', '').replace('\t', '').replace(' ', '')

def normallist(s):
    return s.replace('[ ', '[').replace(' ]', ']')


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
        
        # If with this_is_js()
        assert '5' in py2js('if this_is_js_xx(): 4\nelse: 5')
        assert '5' not in py2js('if this_is_js(): 4\nelse: 5')
    
    def test_for(self):
        
        # Test all possible ranges
        line = nowhitespace(py2js('for i in range(9): pass', inline_stdlib=False))
        assert line == 'vari;for(i=0;i<9;i+=1){}'
        line = nowhitespace(py2js('for i in range(2, 99): pass', inline_stdlib=False))
        assert line == 'vari;for(i=2;i<99;i+=1){}'
        line = nowhitespace(py2js('for i in range(100, 0, -1): pass', inline_stdlib=False))
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
        
        # Range with complex input
        assert evalpy('for i in range(sum([2, 3])): print(i)') == '0\n1\n2\n3\n4'
        
        # Test explicit for-array iteration
        code = py2js('a=[7,8]\nfor i in range(len(a)):\n  print(a[i])')
        assert ' in ' not in code and evaljs(code) == '7\n8'
        # Test enumeration over arrays - should use actual for-loop
        code = py2js('for k in [7, 8]:\n  print(k)')
        assert ' in ' not in code and evaljs(code) == '7\n8'
        # compile time tests
        raises(JSError, py2js, 'for i, j in range(10): pass')
        
        # Test enumeration over dicts
        # Python cannot see its a dict, and uses a for-loop
        code = py2js('d = {3:7, 4:8}\nfor k in d:\n  print(k)')
        assert ' in ' not in code and evaljs(code) == '3\n4'
        code = py2js('d = {3:7, 4:8}\nfor k in d:\n  print(d[k])')
        assert ' in ' not in code and evaljs(code) == '7\n8'
        # .keys()
        code = py2js('d = {3:7, 4:8}\nfor k in d.keys():\n  print(d[k])')
        assert evaljs(code) == '7\n8'  # and ' in ' in code
        # .values()
        code = py2js('d = {3:7, 4:8}\nfor v in d.values():\n  print(v)')
        assert ' in ' in code and evaljs(code) == '7\n8'
        # .items()
        code = py2js('d = {3:7, 4:8}\nfor k,v in d.items():\n  print(k)')
        assert ' in ' in code and evaljs(code) == '3\n4'
        code = py2js('d = {3:7, 4:8}\nfor k,v in d.items():\n  print(v)')
        assert ' in ' in code and evaljs(code) == '7\n8'
        # compile time tests
        raises(JSError, py2js, 'for i, j in x.keys(): pass')
        raises(JSError, py2js, 'for i, j in x.values(): pass')
        raises(JSError, py2js, 'for i in x.items(): pass')
        raises(JSError, py2js, 'for i, j, k in x.items(): pass')
        
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
        code = py2js(self.method_for)
        assert evaljs('%s method_for()' % code) == 'ok\nok\nnull'
        
        # Tuple iterators
        assert evalpy('for i, j in [[1, 2], [3, 4]]: print(i+j)') == '3\n7'
        assert evalpy('for i, j, k in [[1, 2, 3], [3, 4, 5]]: print(i+j+k)') == '6\n12'
    
    
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
        assert 'while' in line
        
        # Test break and continue
        for9 = 'i=-1\nwhile(i<8):\n  i+=1\n  '
        assert evalpy(for9 + 'if i==4:break\n  print(i)\n0') == '0\n1\n2\n3\n0'
        assert evalpy(for9 + 'if i<6:continue\n  print(i)\n0') == '6\n7\n8\n0'
        # Test else
        assert evalpy(for9 + 'if i==3:break\nelse: print(99)\n0') == '0'
        assert evalpy(for9 + 'if i==30:break\nelse: print(99)\n0') == '99\n0'
    
    
    def test_list_comprehensions(self):
        
        # Simple
        code = '[i for i in [-1, -2, 1, 2, 3]]'
        assert str(eval(code)) == normallist(evalpy(code))
        
        # With ifs
        code = '[i for i in [-1, -2, 1, 2, 3] if i > 0 and i < 3]'
        assert str(eval(code)) == normallist(evalpy(code))
        code = '[i for i in [-1, -2, 1, 2, 3] if i > 0 if i < 3]'
        assert str(eval(code)) == normallist(evalpy(code))
        
        # Double
        code = '[i*j for i in [-1, -2, 1, 2, 3] if i > 0 for j in [1, 10, 100] if j<100]'
        assert str(eval(code)) == normallist(evalpy(code))
        
        # Triple
        code = '[i*j*k for i in [1, 2, 3] for j in [1, 10] for k in [5, 7]]'
        assert str(eval(code)) == normallist(evalpy(code))
        
        # Double args
        code = '[(i, j) for i in [1, 2, 3] for j in [1, 10]]'
        assert str(eval(code)).replace('(', '[').replace(')', ']') == normallist(evalpy(code))
        
        # Double iters
        code = '[(i, j) for i, j in [[1, 2], [3, 4], [5, 6]]]'
        assert str(eval(code)).replace('(', '[').replace(')', ']') == normallist(evalpy(code))

class TestExceptions:
    
    def test_raise(self):
        
        assert 'throw' in py2js('raise MyException("foo")')
        assert 'MyException' in py2js('raise MyException("foo")')
        assert 'foo' in py2js('raise MyException("foo")')
        
        catcher = 'try { %s } catch(err) { console.log(err); }'
        assert evaljs(catcher % py2js('raise "foo"')) == 'foo'
        assert evaljs(catcher % py2js('raise 42')) == '42'
        assert evaljs(catcher % py2js('raise ValueError')).count('ValueError')
        assert evaljs(catcher % py2js('raise ValueError("foo")')).count('foo')
        assert evaljs(catcher % py2js('xx = "bar"; raise xx;')).count('bar')
    
    def test_assert(self):
        
        assert 'throw' in py2js('assert True')
        evalpy('assert true; 7') == '7'
        evalpy('assert true, "msg"; 7') == '7'
        
        catcher = 'try { %s } catch(err) { console.log(err); }'
        assert evaljs(catcher % py2js('assert false')).count('AssertionError')
        assert evaljs(catcher % py2js('assert false, "foo"')).count('foo')
    
    def test_catching(self):
        
        def catchtest(x):
            try:
                if x == 1:
                    raise ValueError('foo')
                elif x == 2:
                    raise RuntimeError('foo')
                else:
                    raise "oh crap"
            except ValueError:
                print('value-error')
            except RuntimeError:
                print('runtime-error')
            except Exception:
                print('other-error')
            return undefined
        
        assert evaljs(py2js(catchtest, 'f') + 'f(1)') == 'value-error'
        assert evaljs(py2js(catchtest, 'f') + 'f(2)') == 'runtime-error'
        assert evaljs(py2js(catchtest, 'f') + 'f(3)') == 'other-error'
    
    def test_catching2(self):
        
        def catchtest(x):
            try:
                raise ValueError('foo')
            except Exception as err:
                print(err.message)
            return undefined
        
        assert evaljs(py2js(catchtest, 'f') + 'f(1)').endswith('foo')
    
    def test_finally(self):
        
        def catchtest(x):
            try:
                
                try:
                    raise ValueError('foo')
                finally:
                    print('xx')
                    
            except Exception as err:
                print('yy')
            return undefined
        
        assert evaljs(py2js(catchtest, 'f') + 'f(1)').endswith('xx\nyy')


def func1():
    return 2 + 3


class TestFunctions:
    
    def test_func_default_return_null(self):
        assert evalpy('def foo():pass\nprint(foo(), 1)') == 'null 1'
        assert evalpy('def foo():return\nprint(foo(), 1)') == 'null 1'
    
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
        code = py2js(func1)
        lines = [line for line in code.split('\n') if line]
        
        assert len(lines) == 4  # only three lines + definition
        assert lines[1] == 'func1 = function flx_func1 () {'  # no args
        assert lines[2].startswith('  ')  # indented
        assert lines[3] == '};'  # dedented
    
    
    def method1(self):
        return
    
    def test_method1(self):
        code = py2js(self.method1)
        lines = [line for line in code.split('\n') if line]
        
        assert len(lines) == 4  # only three lines + definition
        assert lines[1] == 'method1 = function () {'  # no args, no self/this
        assert lines[2].startswith('  ')  # indented
        assert lines[3] == '};'  # dedented
    
    def test_default_args(self):
        
        def func(self, foo, bar=2):
            return foo - bar
        
        code = py2js(func)
        lines = [line for line in code.split('\n') if line]
        
        assert lines[1] == 'func = function (foo, bar) {'
        assert '2' in code
        
        assert evaljs(code + 'func(2)') == '0'
        assert evaljs(code + 'func(4, 3)') == '1'
        assert evaljs(code + 'func(0, 0)') == '0'
    
    def test_var_args1(self):
        
        def func(self, *args):
            return args
        
        code1 = py2js(func)
        # lines = [line for line in code1.split('\n') if line]
        
        code2 = py2js('func(2, 3)')
        assert evaljs(code1 + code2, False) == '[2,3]'
        code2 = py2js('func()')
        assert evaljs(code1 + code2, False) == '[]'
        code2 = py2js('a=[2,3]\nfunc(*a)')
        assert evaljs(code1 + code2, False) == '[2,3]'
        code2 = py2js('a=[2,3]\nfunc(1,2,*a)')
        assert evaljs(code1 + code2, False) == '[1,2,2,3]'
    
    def test_var_args2(self):
        
        def func(self, foo, *args):
            return args
        
        code1 = py2js(func)
        #lines = [line for line in code1.split('\n') if line]
        
        code2 = py2js('func(0, 2, 3)')
        assert evaljs(code1 + code2, False) == '[2,3]'
        code2 = py2js('func(0)')
        assert evaljs(code1 + code2, False) == '[]'
        code2 = py2js('a=[0,2,3]\nfunc(*a)')
        assert evaljs(code1 + code2, False) == '[2,3]'
        code2 = py2js('a=[2,3]\nfunc(0,1,2,*a)')
        assert evaljs(code1 + code2, False) == '[1,2,2,3]'
    
    def test_self_becomes_this(self):
        
        def func(self):
            return self.foo
        
        code = py2js(func)
        lines = [line.strip() for line in code.split('\n') if line]
        assert 'return this.foo;' in lines
    
    def test_lambda(self):
        assert evalpy('f=lambda x:x+1\nf(2)') == '3'
        assert evalpy('(lambda x:x+1)(2)') == '3'
    
    def test_scope(self):
        
        def func(self):
            def foo(z):
                y = 2
                stub = False  # noqa
                only_here = 1  # noqa
                return x + y + z
            x = 1
            y = 0
            y = 1  # noqa
            z = 1  # noqa
            res = foo(3)
            stub = True  # noqa
            return res + y  # should return 1+2+3+1 == 7
        
        # Find function start
        code = py2js(func)
        i = code.splitlines().index('var func;')
        assert i >= 0
        
        # Find first lines of functions, where the vars are defined
        vars1 = code.splitlines()[i+2]
        vars2 = code.splitlines()[i+4]
        assert vars1.strip().startswith('var ')
        assert vars2.strip().startswith('var ')
        
        assert 'y' in vars1 and 'y' in vars2
        assert 'stub' in vars1 and 'stub' in vars2
        assert 'only_here' in vars2 and 'only_here' not in vars1
        assert evaljs(code + 'func()') == '7'
    
    def test_scope2(self):
        # Avoid regression for bug with lambda and scoping
        
        def func1(self):
            x = 1
        
        def func2(self):
            x = 1
            y = lambda : None
        
        def func3(self):
            x = 1
            def y():
                pass
        
        assert 'var x' in py2js(func1)
        assert 'var x' in py2js(func2)
        assert 'var x' in py2js(func3)
    
    def test_recursion(self=None):
        
        code = 'def f(i): i *= 2; return i if i > 10 else f(i)\n\n'
        assert evalpy(code + 'f(1)') == '16'
        
        clscode = 'class G:\n  def __init__(self): self.i = 1\n\n'
        code = clscode + '  def f(self): self.i *= 2; return self.i if self.i > 10 else self.f()\n\n'
        assert evalpy(code + 'g = G(); g.f()') == '16'
        
        code = clscode + '  def f(self):\n    def h(): self.i *= 2; return self.i if self.i > 10 else h()\n\n'
        assert evalpy(code + '    return h()\n\ng = G(); g.f()') == '16'
    
    def test_global(self):
        assert py2js('global foo;foo = 3').strip() == 'foo = 3;'
        
        def func1():
            def inner():
                x = 3
            x = 2
            inner()
            return x
        
        def func2():
            def inner():
                global x
                x = 3
            x = 2
            inner()
            return x
    
        assert evaljs(py2js(func1)+'func1()') == '2'
        assert evaljs(py2js(func2)+'func2()') == '3'
    
    @skipif(sys.version_info < (3,), reason='no nonlocal on legacy Python')
    def test_nonlocal(self):
        assert py2js('nonlocal foo;foo = 3').strip() == 'foo = 3;'
        
        func3_code = """def func3():
            def inner():
                nonlocal x
                x = 3
            x = 2
            inner()
            return x
        """
        assert evaljs(py2js(func3_code)+'func3()') == '3'
    
    def test_raw_js(self):
        
        def func(a, b):
            RawJS("""
            var c = 3;
            return a + b + c;
            """)
        
        code = py2js(func)
        assert evaljs(code + 'func(100, 10)') == '113'
        assert evaljs(code + 'func("x", 10)') == 'x103'
    
    def test_docstring(self):
        # And that its not interpreted as raw js
        
        def func(a, b):
            """ docstring """
            return a + b
        
        code = py2js(func)
        assert evaljs(code + 'func(100, 10)') == '110'
        assert evaljs(code + 'func("x", 10)') == 'x10'
        
        assert code.count('// docstring') == 1


class TestClasses:
    
    
    def test_class(self):
        
        class MyClass:
            """ docstring """
            foo = 7
            foo = foo + 1
            
            def __init__(self):
                self.bar = 7
            def addOne(self):
                self.bar += 1
        
        code = py2js(MyClass) + 'var m = new MyClass();'
        
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
                super(MyClass3, self).add(4)  # Use legacy Python syntax
        
        code = py2js(MyClass1) + py2js(MyClass2) + py2js(MyClass3)
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
    
    
    def test_inheritance_super_more(self):
        
        class MyClass4:
            def foo(self):
                return self
        
        class MyClass5(MyClass4):
            def foo(self, test):
                return super().foo()
        
        def foo():
            return super().foo()
        
        code = py2js(MyClass4) + py2js(MyClass5)
        code += py2js(foo).replace('super()', 'MyClass4.prototype')
        code += 'var m4=new MyClass4(), m5=new MyClass5();'
        
        assert evaljs(code + 'm4.foo() === m4') == 'true'
        assert evaljs(code + 'm4.foo() === m4') == 'true'
        assert evaljs(code + 'foo.call(m4) === m4') == 'true'
    
    def test_calling_method_from_init(self):
        
        # Note that all class names inside a module need to be unique
        # for js() to find the correct source.
        
        class MyClass11:
            def __init__(self):
                self._res = self.m1() + self.m2() + self.m3()
            def m1(self):
                return 100
            def m2(self):
                return 10
        
        class MyClass12(MyClass11):
            def m2(self):
                return 20
            def m3(self):
                return 2
        
        code = py2js(MyClass11) + py2js(MyClass12)
        assert evaljs(code + 'var m = new MyClass12(); m._res') == '122'
        assert evaljs(code + 'var m = new MyClass12(); m.m1()') == '100'
    
    def test_ensure_use_new(self):
        class MyClass13:
            def __init__(self):
               pass
        code = py2js(MyClass13)
        err = 'Class constructor is called as a function.'
        assert evaljs(code + 'try { var m = new MyClass13(); "ok"} catch (err) { err; }') == 'ok'
        assert evaljs(code + 'try { var m = MyClass13();} catch (err) { err; }') == err
        assert evaljs(code + 'try { MyClass13.apply(root);} catch (err) { err; }') == err
        assert evaljs(code + 'var window = root;try { MyClass13.apply(window);} catch (err) { err; }') == err
        
    
    def test_bound_methods(self):
        
        class MyClass14:
            def __init__(self):
                self.a = 1
            def add2(self):
                self.a += 2
        
        class MyClass15(MyClass14):
            def add3(self):
                self.a += 3
        
        code = py2js(MyClass14) + py2js(MyClass15)
        assert evaljs(code + 'var m = new MyClass14(); m.add2(); m.add2(); m.a') == '5'
        assert evaljs(code + 'var m = new MyClass14(); var f = m.add2; f(); f(); m.a') == '5'
        assert evaljs(code + 'var m = new MyClass15(); var f = m.add3; f(); f(); m.a') == '7'
        assert evaljs(code + 'var m = new MyClass15(); var f2 = m.add2, f3 = m.add3; f2(); f3(); m.a') == '6'
    
    
    def test_bound_funcs_in_methods(self):
        class MyClass16:
            def foo1(self):
                self.a = 3
                f = lambda i: self.a
                return f()
            
            def foo2(self):
                self.a = 3
                def bar():
                    return self.a
                return bar()
            
            def foo3(self):
                self.a = 3
                def bar(self):
                    return self.a
                return bar()
        
        code = py2js(MyClass16)
        assert evaljs(code + 'var m = new MyClass16(); m.foo1()') == '3'
        assert evaljs(code + 'var m = new MyClass16(); m.foo2()') == '3'
        assert evaljs(code + 'var m = new MyClass16(); try {m.foo3();} catch (err) {"ok"}') == 'ok'


run_tests_if_main()
