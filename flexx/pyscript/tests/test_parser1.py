from flexx.util.testing import run_tests_if_main, raises

from flexx import pyscript
from flexx.pyscript import JSError, py2js, evaljs, evalpy, Parser


def nowhitespace(s):
    return s.replace('\n', '').replace('\t', '').replace(' ', '')


class TestParser(Parser):
    
    def function_foo_foo(self, node):
        return 'xxx'
    
    def method_bar_bar(self, node, base):
        return base


class TestTheParser:
    
    def test_special_functions(self):
        assert TestParser("foo_foo()").dump() == 'xxx;'
        assert TestParser("bar_bar()").dump() == 'bar_bar();'
        
        assert TestParser("xxx.bar_bar()").dump() == 'xxx;'
        assert TestParser("xxx.foo_foo()").dump() == 'xxx.foo_foo();'
    
    def test_exceptions(self):
        raises(JSError, py2js, "foo(**kwargs)")
        

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
        
        # No parentices around names, numbers and strings
        assert py2js('foo - bar') == "foo - bar;"
        assert py2js('_foo3 - _bar4') == "_foo3 - _bar4;"
        assert py2js('3 - 4') == "3 - 4;"
        assert py2js('"abc" - "def"') == '"abc" - "def";'
        assert py2js("'abc' - 'def'") == '"abc" - "def";'
        assert py2js("'\"abc\" - \"def\"'") == '"\\"abc\\" - \\"def\\"";'
        
        # But they should be if it gets more complex
        assert py2js('foo - bar > 4') == "(foo - bar) > 4;"
        
        # Test outcome
        assert evalpy('2+3') == '5'  # Binary
        assert evalpy('6/3') == '2'
        assert evalpy('4//3') == '1'
        assert evalpy('2**8') == '256'
        assert evalpy('not True') == 'false'  # Unary
        assert evalpy('- 3') == '-3'
        assert evalpy('True and False') == 'false'  # Boolean
        assert evalpy('True or False') == 'true'
        # Bug
        assert evalpy('(9-3-3)/3') == '1'
        
        # string formatting
        assert evalpy('"%s" % "bar"') == 'bar'
        assert evalpy('"-%s-" % "bar"') == '-bar-'
        assert evalpy('"foo %s foo" % "bar"') == 'foo bar foo'
        assert evalpy('"x %i" % 6') == 'x 6'
        assert evalpy('"x %f" % 6') == 'x 6'
        assert evalpy('"%s: %f" % ("value", 6)') == 'value: 6'
        assert evalpy('"%r: %r" % ("value", 6)') == '"value": 6'
    
    def test_overloaded_list_ops(self):
        assert evalpy('[1, 2] + [3, 4]') == '[ 1, 2, 3, 4 ]'
        assert evalpy('[3, 4] + [1, 2]') == '[ 3, 4, 1, 2 ]'
        assert evalpy('"ab" + "cd"') == 'abcd'
        assert evalpy('[3, 4] * 2') == '[ 3, 4, 3, 4 ]'
        assert evalpy('2 * [3, 4]') == '[ 3, 4, 3, 4 ]'
        assert evalpy('"ab" * 2') == 'abab'
        assert evalpy('2 * "ab"') == 'abab'
        
        assert evalpy('a = [1, 2]; a += [3, 4]; a') == '[ 1, 2, 3, 4 ]'
        assert evalpy('a = [3, 4]; a += [1, 2]; a') == '[ 3, 4, 1, 2 ]'
        assert evalpy('a = [3, 4]; a *= 2; a') == '[ 3, 4, 3, 4 ]'
        assert evalpy('a = "ab"; a *= 2; a') == 'abab'
    
    def test_raw_js_overloading(self):
        # more RawJS tests in test_parser3.py
        s1 = 'a=3; b=4; c=1; a + b - c'
        s2 = 'a=3; b=4; c=1; RawJS("a + b") - c'
        assert evalpy(s1) == '6'
        assert evalpy(s2) == '6'
        assert 'pyfunc' in py2js(s1)
        assert 'pyfunc' not in py2js(s2)
    
    def test_overload_funcs_dont_overload_real_funcs(self):
        assert evalpy('def add(a, b): return a-b\n\nadd(4, 1)') == '3'
        assert evalpy('def op_add(a, b): return a-b\n\nop_add(4, 1)') == '3'
    
    def test_comparisons(self):
        
        assert py2js('4 > 3') == '4 > 3;'
        assert py2js('4 is 3') == '4 === 3;'
        
        assert evalpy('4 > 4') == 'false'
        assert evalpy('4 >= 4') == 'true'
        assert evalpy('4 < 3') == 'false'
        assert evalpy('4 <= 4') == 'true'
        assert evalpy('4 == 3') == 'false'
        assert evalpy('4 != 3') == 'true'
        
        assert evalpy('4 == "4"') == 'true'  # yuck!
        assert evalpy('4 is "4"') == 'false'
        assert evalpy('4 is not "4"') == 'true'
        
        assert evalpy('"c" in "abcd"') == 'true'
        assert evalpy('"x" in "abcd"') == 'false'
        assert evalpy('"x" not in "abcd"') == 'true'
        
        assert evalpy('3 in [1,2,3,4]') == 'true'
        assert evalpy('9 in [1,2,3,4]') == 'false'
        assert evalpy('9 not in [1,2,3,4]') == 'true'
        
        assert evalpy('"bar" in {"foo": 3}') == 'false'
        assert evalpy('"foo" in {"foo": 3}') == 'true'
        
        # was a bug
        assert evalpy('not (1 is null and 1 is null)') == 'true'
    
    def test_deep_comparisons(self):
        # List
        arr = '[(1,2), (3,4), (5,6), (1,2), (7,8)]\n'
        assert evalpy('a=' + arr + '(1,2) in a') == 'true'
        assert evalpy('a=' + arr + '(7,8) in a') == 'true'
        assert evalpy('a=' + arr + '(3,5) in a') == 'false'
        assert evalpy('a=' + arr + '3 in a') == 'false'
        
        assert evalpy('(2, 3) == (2, 3)') == 'true'
        assert evalpy('[2, 3] == [2, 3]') == 'true'
        assert evalpy('a=' + arr + 'b=' + arr + 'a==b') == 'true'
        
        # Dict
        dct = '{"a":7, 3:"foo", "bar": 1, "9": 3}\n'
        assert evalpy('d=' + dct + '"a" in d') == 'true'
        assert evalpy('d=' + dct + '"3" in d') == 'true'
        assert evalpy('d=' + dct + '3 in d') == 'true'
        assert evalpy('d=' + dct + '"bar" in d') == 'true'
        assert evalpy('d=' + dct + '9 in d') == 'true'
        assert evalpy('d=' + dct + '"9" in d') == 'true'
        assert evalpy('d=' + dct + '7 in d') == 'false'
        assert evalpy('d=' + dct + '"1" in d') == 'false'
        
        assert evalpy('{2: 3} == {"2": 3}') == 'true'
        assert evalpy('dict(foo=7) == {"foo": 7}') == 'true'
        assert evalpy('a=' + dct + 'b=' + dct + 'a==b') == 'true'
        assert evalpy('{"foo": 1, "bar": 2}=={"bar": 2, "foo": 1}') == 'true'
        assert evalpy('{"bar": 2, "foo": 1}=={"foo": 1, "bar": 2}') == 'true'
        
        # Deeper
        d1 = 'd1={"foo": [2, 3, {1:2,3:4,5:["aa", "bb"]}], "bar": None}\n'
        d2 = 'd2={"bar": None, "foo": [2, 3, {5:["aa", "bb"],1:2,3:4}]}\n'  # same
        d3 = 'd3={"foo": [2, 3, {1:2,3:4,5:["aa", "b"]}], "bar": None}\n'  # minus b
        assert evalpy(d1+d2+d3+'d1 == d2') == 'true'
        assert evalpy(d1+d2+d3+'d2 == d1') == 'true'
        assert evalpy(d1+d2+d3+'d1 != d2') == 'false'
        assert evalpy(d1+d2+d3+'d1 == d3') == 'false'
        assert evalpy(d1+d2+d3+'d1 != d3') == 'true'
        #
        assert evalpy(d1+d2+d3+'d2 in [2, d1, 4]') == 'true'
        assert evalpy(d1+d2+d3+'d2 in ("xx", d2, None)') == 'true'
        assert evalpy(d1+d2+d3+'d2 not in (1, d3, 2)') == 'true'
        assert evalpy(d1+d2+d3+'4 in [2, d1, 4]') == 'true'
    
    def test_truthfulness_of_basic_types(self):
        # Numbers
        assert evalpy('"T" if (1) else "F"') == 'T'
        assert evalpy('"T" if (0) else "F"') == 'F'
        
        # Strings
        assert evalpy('"T" if ("a") else "F"') == 'T'
        assert evalpy('"T" if ("") else "F"') == 'F'
        
        # None - undefined
        assert evalpy('None is null') == 'true'
        assert evalpy('None is undefined') == 'false'
        assert evalpy('undefined is undefined') == 'true'
    
    def test_truthfulness_of_array_and_dict(self):
        
        # Arrays
        assert evalpy('bool([1])') == 'true'
        assert evalpy('bool([])') == 'false'
        #
        assert evalpy('"T" if ([1, 2, 3]) else "F"') == 'T'
        assert evalpy('"T" if ([]) else "F"') == 'F'
        #
        assert evalpy('if [1]: "T"\nelse: "F"') == 'T'
        assert evalpy('if []: "T"\nelse: "F"') == 'F'
        #
        assert evalpy('if [1] and 1: "T"\nelse: "F"') == 'T'
        assert evalpy('if [] and 1: "T"\nelse: "F"') == 'F'
        assert evalpy('if [] or 1: "T"\nelse: "F"') == 'T'
        #
        assert evalpy('[2] or 42') == '[ 2 ]'
        assert evalpy('[] or 42') == '42'
        
        # Dicts
        assert evalpy('bool({1:2})') == 'true'
        assert evalpy('bool({})') == 'false'
        #
        assert evalpy('"T" if ({"foo": 3}) else "F"') == 'T'
        assert evalpy('"T" if ({}) else "F"') == 'F'
        #
        assert evalpy('if {1:2}: "T"\nelse: "F"') == 'T'
        assert evalpy('if {}: "T"\nelse: "F"') == 'F'
        #
        assert evalpy('if {1:2} and 1: "T"\nelse: "F"') == 'T'
        assert evalpy('if {} and 1: "T"\nelse: "F"') == 'F'
        assert evalpy('if {} or 1: "T"\nelse: "F"') == 'T'
        #
        assert evalpy('{1:2} or 42') == "{ '1': 2 }"
        assert evalpy('{} or 42') == '42'
        assert evalpy('{} or 0') == '0'
        assert evalpy('None or []') == '[]'
        
        # Eval extra types
        assert evalpy('null or 42') == '42'
        assert evalpy('ArrayBuffer(4) or 42') != '42'
        
        # No bools
        assert py2js('if foo: pass').count('_truthy')
        assert py2js('if foo.length: pass').count('_truthy') == 0
        assert py2js('if 3: pass').count('_truthy') == 0
        assert py2js('if True: pass').count('_truthy') == 0
        assert py2js('if a == 3: pass').count('_truthy') == 0
        assert py2js('if a is 3: pass').count('_truthy') == 0
        
    
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
        assert py2js('foo[i] = 3') == 'foo[i] = 3;'  # without var
        
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
        
        # For unpacking, test that variables are declared, but not when attr or index
        assert py2js('xx, yy = 3, 4').count('xx') == 2
        assert py2js('xx[0], yy[0] = 3, 4').count('xx') == 1
        assert py2js('xx.a, yy.a = 3, 4').count('xx') == 1
        
        # Class variables don't get a var
        code = py2js('class Foo:\n  bar=3\n  bar = bar + 1')
        assert code.count('bar') == 3
        assert code.count('Foo.prototype.bar') == 3
    
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
        
        assert py2js('"bla\\"bla"') == '"bla\\"bla";'
        assert py2js('3') == '3;'
        assert py2js('3.1415') == '3.1415;'
        
        assert py2js('[1,2,3]') == '[1, 2, 3];'
        assert py2js('(1,2,3)') == '[1, 2, 3];'
        assert py2js('{foo: 3, bar: 4}') == '{foo: 3, bar: 4};'
    
    def test_ignore_import_of_compiler(self):
        modname = pyscript.__name__
        assert py2js('from %s import x, y, z\n42' % modname) == '42;'
    
    def test_import(self):
        with raises(JSError):
            py2js('import time')
        
        # But we do support special time funcs
        import time
        assert abs(float(evalpy('time()')) - time.time()) < 0.5
        evalpy('t0=perf_counter(); t1=perf_counter(); (t1-t0)').startswith('0.0')
    
    def test_funcion_call(self):
        jscode = 'var foo = function (x, y) {return x+y;};'
        assert evaljs(jscode + py2js('foo(2,2)')) == '4'
        assert evaljs(jscode + py2js('foo("so ", True)')) == 'so true'
        assert evaljs(jscode + py2js('a=[1,2]; foo(*a)')) == '3'
        assert evaljs(jscode + py2js('a=[1,2]; foo(7, *a)')) == '8'
        
        # Test super (is tested for real in test_parser3.py
        assert evalpy('d={"_base_class": console};d._base_class.log(4)') == '4'
        assert evalpy('d={"_base_class": console};d._base_class.log()') == ''
        
        jscode = 'var foo = function () {return this.val};'
        jscode += 'var d = {"foo": foo, "val": 7};\n'
        assert evaljs(jscode + py2js('d["foo"]()')) == '7'
        assert evaljs(jscode + py2js('d["foo"](*[3, 4])')) == '7'
    
    def test_instantiation(self):
        # Test creating instances
        assert 'new' in py2js('a = Bar()')
        assert 'new' in py2js('a = x.Bar()')
        assert 'new' not in py2js('a = foo()')
        assert 'new' not in py2js('a = _foo()')
        assert 'new' not in py2js('a = _Foo()')
        assert 'new' not in py2js('a = this.Bar()')
        assert 'new' not in py2js('a = JSON.stringify(x)')
        
        jscode = 'function Bar() {this.x = 3}\nvar x=1;\n'
        assert evaljs(jscode + py2js('a=Bar()\nx')) == '1'
        
        # Existing classes and functions are used to determine if a
        # call is an instantiation
        assert 'new'     in py2js('class foo:pass\na = foo()')
        assert 'new' not in py2js('class foo:pass\ndef foo():pass\na = foo()')
        assert 'new' not in py2js('def foo():pass\nclass foo:pass\na = foo()')
        #
        assert 'new' not in py2js('def Bar():pass\na = Bar()')
        assert 'new'     in py2js('def Bar():pass\nclass Bar:pass\na = Bar()')
        assert 'new'     in py2js('class Bar:pass\ndef Bar():pass\na = Bar()')
    
    def test_pass(self):
        assert py2js('pass') == ''
    
    def test_delete(self):
        assert evalpy('d={}\nd.foo=3\n\nd') == "{ foo: 3 }"
        assert evalpy('d={}\nd.foo=3\ndel d.foo\nd') == '{}'
        assert evalpy('d={}\nd.foo=3\nd.bar=3\ndel d.foo\nd') == '{ bar: 3 }'
        assert evalpy('d={}\nd.foo=3\nd.bar=3\ndel d.foo, d["bar"]\nd') == '{}'
        

class TestModules:
    
    def test_module(self):
        
        code = Parser('"docstring"\nfoo=3;bar=4;_priv=0;', 'foo.py').dump()
        
        # Has docstring
        assert code.count('// docstring') == 1


run_tests_if_main()
