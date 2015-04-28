from pytest import raises
from flexx.util.testing import run_tests_if_main

from flexx.pyscript import JSError, py2js, evaljs, evalpy, Parser
from flexx import pyscript


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
        
        # string formatting
        assert evalpy('"%s" % "bar"') == 'bar'
        assert evalpy('"-%s-" % "bar"') == '-bar-'
        assert evalpy('"foo %s foo" % "bar"') == 'foo bar foo'
        assert evalpy('"x %i" % 6') == 'x 6'
        assert evalpy('"x %f" % 6') == 'x 6'
        assert evalpy('"%s: %f" % ("value", 6)') == 'value: 6'
    
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
        
        assert py2js('"bla\\"bla"') == "'bla\"bla';"
        assert py2js('3') == '3;'
        assert py2js('3.1415') == '3.1415;'
        
        assert py2js('[1,2,3]') == '[1, 2, 3];'
        assert py2js('(1,2,3)') == '[1, 2, 3];'
        assert py2js('{foo: 3, bar: 4}') == '{foo: 3, bar: 4};'
    
    def test_ignore_import_of_compiler(self):
        modname = pyscript.__name__
        assert py2js('from %s import x, y, z\n42' % modname) == '42;'
    
    def test_funcion_call(self):
        jscode = 'var foo = function (x, y) {return x+y;};'
        assert evaljs(jscode + py2js('foo(2,2)')) == '4'
        assert evaljs(jscode + py2js('foo("so ", True)')) == 'so true'
        assert evaljs(jscode + py2js('a=[1,2]; foo(*a)')) == '3'
        
        # Test super (is tested for real in test_parser3.py
        assert evalpy('d={"_base_class": console};d._base_class.log(4)') == '4'
        assert evalpy('d={"_base_class": console};d._base_class.log()') == ''
        
        jscode = 'var foo = function () {return this.val};'
        jscode += 'var d = {"foo": foo, "val": 7};\n'
        assert evaljs(jscode + py2js('d["foo"]()')) == '7'
        assert evaljs(jscode + py2js('d["foo"](*[3, 4])')) == '7'
    
    def test_instantiation(self):
        # Test creating instances
        assert 'new' in py2js('a = Foo()')
        assert 'new' not in py2js('a = foo()')
        assert 'new' not in py2js('a = _foo()')
        assert 'new' not in py2js('a = _Foo()')
        assert 'new' not in py2js('a = this.Foo()')
        assert 'new' not in py2js('a = JSON.stringify(x)')
        
        jscode = 'function Foo() {this.x = 3}\nx=1;\n'
        assert evaljs(jscode + py2js('a=Foo()\nx')) == '1'
        
    def test_pass(self):
        assert py2js('pass') == ''
    
    def test_delete(self):
        assert evalpy('d={}\nd.foo=3\n\nd') == "{ foo: 3 }"
        assert evalpy('d={}\nd.foo=3\ndel d.foo\nd') == '{}'
        assert evalpy('d={}\nd.foo=3\nd.bar=3\ndel d.foo\nd') == '{ bar: 3 }'
        assert evalpy('d={}\nd.foo=3\nd.bar=3\ndel d.foo, d["bar"]\nd') == '{}'
        

class TestModules:
    
    def test_module(self):
        
        code = Parser('"docstring"\nfoo=3;bar=4;_priv=0;', 'mymodule').dump()
        
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
