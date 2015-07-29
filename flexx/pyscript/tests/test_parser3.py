
from pytest import raises
from flexx.util.testing import run_tests_if_main

from flexx.pyscript import JSError, py2js, evaljs, evalpy


def nowhitespace(s):
    return s.replace('\n', '').replace('\t', '').replace(' ', '')


class TestHardcoreBuildins:
    
    def test_isinstance(self):
        # The resulting code is not particularly pretty, so we just
        # test outcome
        
        assert evalpy('isinstance(3.0, list) == True') == 'false'
        assert evalpy('isinstance(3.0, float) == True') == 'true'
        
        assert evalpy('x={}; isinstance(x.foo, "undefined")') == 'true'
        
        assert evalpy('isinstance(None, "null")') == 'true'
        assert evalpy('isinstance(undefined, "undefined")') == 'true'
        #
        assert evalpy('isinstance(None, "undefined")') == 'false'
        assert evalpy('isinstance(undefined, "null")') == 'false'
        
        assert evalpy('isinstance(3, float)') == 'true'
        assert evalpy('isinstance(3, (int, float))') == 'true'
        assert evalpy('isinstance(3, "number")') == 'true'
        #
        #assert evalpy('isinstance(3, int)') == 'false'  # int is not defined
        
        assert evalpy('isinstance("", str)') == 'true'
        assert evalpy('isinstance("", "string")') == 'true'
        #
        assert evalpy('isinstance("", list)') == 'false'
        
        assert evalpy('isinstance(True, bool)') == 'true'
        assert evalpy('isinstance(True, "boolean")') == 'true'
        #
        assert evalpy('isinstance(True, float)') == 'false'
        
        assert evalpy('isinstance([], list)') == 'true'
        assert evalpy('isinstance([], "array")') == 'true'
        #
        assert evalpy('isinstance([], "object")') == 'false'
        assert evalpy('isinstance([], "Object")') == 'false'
        assert evalpy('isinstance([], dict)') == 'false'
        
        assert evalpy('isinstance({}, dict)') == 'true'
        assert evalpy('isinstance({}, "object")') == 'true'
        #
        assert evalpy('isinstance({}, list)') == 'false'
        assert evalpy('isinstance({}, "array")') == 'false'
        
        assert evalpy('isinstance(eval, types.FunctionType)') == 'true'
        assert evalpy('isinstance(eval, FunctionType)') == 'true'
        assert evalpy('isinstance(3, types.FunctionType)') == 'false'
        
        # own class
        code = 'function MyClass () {return this;}\nx = new MyClass();\n'
        assert evaljs(code + py2js('isinstance(x, "object")')) == 'true'
        assert evaljs(code + py2js('isinstance(x, "Object")')) == 'true'
        assert evaljs(code + py2js('isinstance(x, "MyClass")')) == 'true'
        assert evaljs(code + py2js('isinstance(x, MyClass)')) == 'true'
    
    def test_hasattr(self):
        code = 'a = {"foo":1, "bar":2};\n'
        assert evalpy(code + 'hasattr(a, "foo")') == 'true'
        assert evalpy(code + 'hasattr(a, "fooo")') == 'false'
    
    def test_getattr(self):
        code = 'a = {"foo":1, "bar":2};\n'
        assert evalpy(code + 'getattr(a, "foo")') == '1'
        assert evalpy(code + 'getattr(a, "bar")') == '2'
        exc_att = 'except AttributeError: print("err")'
        assert evalpy(code + 'try:\n  getattr(a, "fooo")\n' + exc_att) == 'err'
        assert evalpy(code + 'getattr(a, "fooo", 3)') == '3'
    
    def test_print(self):
        # Test code
        assert py2js('print()') == 'console.log();'
        assert py2js('print(3)') == 'console.log(3);'
        assert py2js('foo.print()') == 'foo.print();'
        
        # Test single
        assert evalpy('print(3)') == '3'
        assert evalpy('print(3); print(3)') == '3\n3'
        assert evalpy('print(); print(3)') == '\n3'  # Test \n
        assert evalpy('print("hello world")') == 'hello world'
        # Test multiple args
        assert evalpy('print(3, "hello")') == '3 hello'
        assert evalpy('print(3+1, "hello", 3+1)') == '4 hello 4'
        # Test sep and end
        assert evalpy('print(3, 4, 5)') == '3 4 5'
        assert evalpy('print(3, 4, 5, sep="")') == '345'
        assert evalpy('print(3, 4, 5, sep="\\n")') == '3\n4\n5'
        assert evalpy('print(3, 4, 5, sep="--")') == '3--4--5'
        assert evalpy('print(3, 4, 5, end="-")') == '3 4 5-'
        assert evalpy('print(3, 4, 5, end="\\n\\n-")') == '3 4 5\n\n-'
        
        raises(JSError, py2js, 'print(foo, file=x)')
        raises(JSError, py2js, 'print(foo, bar=x)')
    
    def test_len(self):
        assert py2js('len(a)') == 'a.length;'
        assert py2js('len(a, b)') == 'len(a, b);'
    
    def test_min(self):
        assert evalpy('min([3, 4, 1, 5, 2])') == '1'
        assert evalpy('min(3, 4, 1, 5, 2)') == '1'
    
    def test_max(self):
        assert evalpy('max([3, 4, 5, 1])') == '5'
        assert evalpy('max(3, 4, 5, 1)') == '5'
    
    def test_callable(self):
        assert evalpy('callable([])') == 'false'
        assert evalpy('callable(3)') == 'false'
        
        assert evalpy('callable(Boolean)') == 'true'
        assert evalpy('callable(eval)') == 'true'
        assert evalpy('def foo():pass\ncallable(foo)') == 'true'
        assert evalpy('foo = lambda x:1\ncallable(foo)') == 'true'


class TestOtherBuildins:
    
    def test_allow_overload(self):
        assert evalpy('sum([3, 4])') == '7'
        assert evalpy('sum = lambda x:1\nsum([3, 4])') == '1'
    
    def test_sum(self):
        assert evalpy('sum([3, 4, 1, 5, 2])') == '15'
    
    def test_round(self):
        assert evalpy('round(3.4)') == '3'
        assert evalpy('round(3.6)') == '4'
        assert evalpy('round(-3.4)') == '-3'
        assert evalpy('round(-3.6)') == '-4'
    
    def test_int(self):
        assert evalpy('int(3.4)') == '3'
        assert evalpy('int(3.6)') == '3'
        assert evalpy('int(-3.4)') == '-3'
        assert evalpy('int(-3.6)') == '-3'
        assert evalpy('"5" + 2') == '52'
        assert evalpy('int("5") + 2') == '7'  # -> evaluate to number
        # Note: on Nodejs "5" * 2 also becomes 10 ...
    
    def test_float(self):
        assert evalpy('"5.2" + 2') == '5.22'
        assert evalpy('float("5") + 2') == '7'
        assert evalpy('float("5.2") + 2') == '7.2'
    
    def test_str(self):
        assert evalpy('str(5) + 2') == '52'
        assert evalpy('str("xx") + 2') == 'xx2'
    
    def test_bool(self):
        assert evalpy('bool(5)') == 'true'
        assert evalpy('bool("xx")') == 'true'
        assert evalpy('bool(0)') == 'false'
        assert evalpy('bool("")') == 'false'
        #
        assert evalpy('bool([1])') == 'true'
        assert evalpy('bool({1:2})') == 'true'
        assert evalpy('bool([])') == 'false'
        assert evalpy('bool({})') == 'false'
    
    def test_abs(self):
        assert evalpy('abs(5)') == '5'
        assert evalpy('abs(0)') == '0'
        assert evalpy('abs(-2)') == '2'
    
    def test_all(self):
        assert evalpy('all([1, 2, 3])') == 'true' 
        assert evalpy('all([0, 2, 3])') == 'false'
        assert evalpy('all([])') == 'true'
    
    def test_any(self):
        assert evalpy('any([1, 2, 3])') == 'true' 
        assert evalpy('any([0, 2, 0])') == 'true'
        assert evalpy('any([0, 0, 0])') == 'false'
        assert evalpy('any([])') == 'false' 


class TestExtra:
    
    def test_perf_counter(self):
        evalpy('t0=perf_counter(); t1=perf_counter(); (t1-t0)').startswith('0.0')


class TestListMethods:
    
    def test_append(self):
        assert nowhitespace(evalpy('a = [2]; a.append(3); a')) == '[2,3]'
    
    def test_remove(self):
        assert nowhitespace(evalpy('a = [2, 3]; a.remove(3); a')) == '[2]'
        assert nowhitespace(evalpy('a = [2, 3]; a.remove(2); a')) == '[3]'
        assert nowhitespace(evalpy('x = {"a":[2, 3]}; x.a.remove(2); x.a')) == '[3]'
        

class TestDictMethods:
    
    def test_get(self):
        assert evalpy('a = {"foo":3}; a.get("foo")') == '3'
        assert evalpy('a = {"foo":3}; a.get("foo", 0)') == '3'
        assert evalpy('a = {"foo":3}; a.get("bar")') == 'null'
        assert evalpy('a = {"foo":3}; a.get("bar", 0)') == '0'
        assert evalpy('{"foo":3}.get("foo")') == '3'
        assert evalpy('{"foo":3}.get("bar", 0)') == '0'
        
        # Test that if a get exists, that one is used
        fun = 'def fun(x): return 42\n'
        assert evalpy(fun + 'a = {"get": fun}; a.get("bar")') == '42'
        
    def test_keys(self):
        assert evalpy('a = {"foo":3}; a.keys()') == "[ 'foo' ]"


class TestStrMethods:
    
    def test_startswith(self):
        assert evalpy('"foobar".startswith("foo")') == "true"
        assert evalpy('"foobar".startswith("bar")') == "false"
        assert evalpy('("fo" + "obar").startswith("foo")') == "true"
        

run_tests_if_main()
