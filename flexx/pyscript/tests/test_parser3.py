import sys
from flexx.util.testing import run_tests_if_main, raises, skip

from flexx.pyscript import JSError, py2js, evaljs, evalpy, RawJS


def nowhitespace(s):
    return s.replace('\n', '').replace('\t', '').replace(' ', '')


def foo(a, b):
    x = RawJS('a + b')
    y = 0
    RawJS("""
    for (i=0; i<8; i++) {
        y += i * x;
    }
    """)
    RawJS("""while (y>0) {
        x += y;
        y -= 1;
    }
    """)


class TestSpecials:
    
    def test_rawJS(self):
        
        code = py2js(foo)
        assert 'pyfunc' not in code
        assert '    x =' in code
        assert '    for' in code
        assert '        y +=' in code
        assert '    while' in code
        assert '        y -=' in code


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
        code = 'function MyClass () {return this;}\nvar x = new MyClass();\n'
        assert evaljs(code + py2js('isinstance(x, "object")')) == 'true'
        assert evaljs(code + py2js('isinstance(x, "Object")')) == 'true'
        assert evaljs(code + py2js('isinstance(x, "MyClass")')) == 'true'
        assert evaljs(code + py2js('isinstance(x, MyClass)')) == 'true'
    
    def test_issubclass(self):
        code = 'class Foo:pass\nclass Bar(Foo): pass\n'
        assert evalpy(code + 'issubclass(Bar, Foo)') == 'true'
        assert evalpy(code + 'issubclass(Foo, Bar)') == 'false'
        assert evalpy(code + 'issubclass(Bar, object)') == 'true'
        
        
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
    
    def test_setattr(self):
        code = 'a = {"foo":1};\n'
        assert evalpy(code + 'setattr(a, "foo", 2); a') == "{ foo: 2 }"
    
    def test_deltattr(self):
        code = 'a = {"foo":1};\n'
        assert evalpy(code + 'delattr(a, "foo")\na') == '{}'
    
    def test_print(self):
        # Test code
        assert py2js('print()') == 'console.log("");'
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

    def test_chr_and_ord(self):
        assert evalpy('chr(65)') == 'A'
        assert evalpy('chr(65+32)') == 'a'
        assert evalpy('ord("A")') == '65'
        assert evalpy('ord("a")') == '97'
    
    def test_list(self):
        assert py2js('list()') == '[];'
        assert evalpy('list("abc")') == "[ 'a', 'b', 'c' ]"
        assert evalpy('list({1:2, 3:4})') == "[ '1', '3' ]"
        assert evalpy('tuple({1:2, 3:4})') == "[ '1', '3' ]"
    
    def test_dict(self):
        assert py2js('dict()') == '{};'
        ok = "{ foo: 1, bar: 2 }", "{ bar: 2, foo: 1 }"
        assert evalpy('dict([["foo", 1], ["bar", 2]])') in ok
        assert evalpy('dict({"foo": 1, "bar": 2})') in ok
    
    def test_range(self):
        assert evalpy('list(range(4))') == '[ 0, 1, 2, 3 ]'
        assert evalpy('list(range(2, 4))') == '[ 2, 3 ]'
        assert evalpy('list(range(2, 9, 2))') == '[ 2, 4, 6, 8 ]'
        assert evalpy('list(range(10, 3, -2))') == '[ 10, 8, 6, 4 ]'


class TestOtherBuildins:
    
    # def test_allow_overload(self):
    #     assert evalpy('sum([3, 4])') == '7'
    #     assert evalpy('sum = lambda x:1\nsum([3, 4])') == '1'
    
    def test_pow(self):
        assert evalpy('pow(2, 3)') == '8'
        assert evalpy('pow(10, 2)') == '100'
    
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
    
    def test_repr(self):
        # The [:] is to ensure the result is a string
        assert evalpy('repr(5)[:]') == '5'
        assert evalpy('repr("abc")') == '"abc"'
        assert evalpy('repr([1, 2, 3])[:]') == "[1,2,3]"
        assert evalpy('repr({1:2})[:]') == '{"1":2}'
    
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
    
    def test_divod(self):
        assert evalpy('divmod(13, 3)') == '[ 4, 1 ]'
        assert evalpy('a, b = divmod(100, 7); print(a); print(b)') == '14\n2'
        
    def test_all(self):
        assert evalpy('all([1, 2, 3])') == 'true' 
        assert evalpy('all([0, 2, 3])') == 'false'
        assert evalpy('all([])') == 'true'
        
        assert evalpy('all([3, [], 3])') == 'false'
        assert evalpy('all([3, [1], 3])') == 'true'
    
    def test_any(self):
        assert evalpy('any([1, 2, 3])') == 'true' 
        assert evalpy('any([0, 2, 0])') == 'true'
        assert evalpy('any([0, 0, 0])') == 'false'
        assert evalpy('any([])') == 'false' 
        
        assert evalpy('any([0, [], 0])') == 'false'
        assert evalpy('any([0, [1], 0])') == 'true'
    
    def test_enumerate(self):
        assert evalpy('for i, x in enumerate([10, 20, 30]): print(i*x)') == '0\n20\n60'
    
    def test_zip(self):
        assert evalpy('for i, x in zip([1, 2, 3], [10, 20, 30]): print(i*x)') == '10\n40\n90'
        res = '111\n222\n333'
        assert evalpy('for a, b, c in zip([1, 2, 3], [10, 20, 30], [100, 200, 300]): print(a+b+c)') == res
    
    def test_reversed(self):
        assert evalpy('for x in reversed([10, 20, 30]): print(x)') == '30\n20\n10'
    
    def test_sorted(self):
        assert evalpy('for x in sorted([1, 9, 3, 2, 7, 8, 4]): print(x)') == '1\n2\n3\n4\n7\n8\n9'
        assert evalpy('for x in reversed(sorted([1, 9, 3, 2, 7, 8, 4])): print(x)') == '9\n8\n7\n4\n3\n2\n1'
        assert evalpy('for x in sorted([1, 9, 3, 2, 7, 8, 4], key=lambda a: -a): print(x)') == '9\n8\n7\n4\n3\n2\n1'
        assert evalpy('for x in sorted([1, 9, 3, 2, 7, 8, 4], reverse=True): print(x)') == '9\n8\n7\n4\n3\n2\n1'
        
        assert evalpy('for x in sorted(["bb", "aa", "mm", "dd"]): print(x)') == 'aa\nbb\ndd\nmm'
        assert evalpy('for x in sorted(["bb", "aa", "mm", "dd"], key=lambda x: x): print(x)') == 'aa\nbb\ndd\nmm'
    
    def test_filter(self):
        assert list(filter(lambda x:x>0, [-1, -2, 1, 2])) == [1, 2]
        
        code = 'f1 = lambda x: x>0\n'
        assert evalpy(code + 'for x in filter(f1, [-1, -2, 0, 1, 2]): print(x)') == '1\n2'
        assert evalpy(code + 'for x in filter(None, [-1, -2, 0, 1, 2]): print(x)') == '-1\n-2\n1\n2'
    
    def test_map(self):
        code = 'f1 = lambda x: x+2\n'
        assert evalpy(code + 'for x in map(f1, [-1, 0, 2]): print(x)') == '1\n2\n4'


class TestListMethods:
    
    def test_append(self):
        assert nowhitespace(evalpy('a = [2]; a.append(3); a')) == '[2,3]'
    
    def test_remove(self):
        code = 'a=[1,2,3,4,3,5];\n'
        assert evalpy(code + 'a.remove(2); a') == '[ 1, 3, 4, 3, 5 ]'
        assert evalpy(code + 'a.remove(3); a') == '[ 1, 2, 4, 3, 5 ]'
        assert 'ValueError' in evalpy(code + 'try:\n  a.remove(9);\nexcept Exception as e:\n  e')
        assert nowhitespace(evalpy('x = {"a":[2, 3]}; x.a.remove(2); x.a')) == '[3]'
        
        assert evalpy('a=[1,(2,3),4]; a.remove((2,3)); a') == '[ 1, 4 ]'
    
    def test_count(self):
        assert evalpy('[1,2,3,4,5,3].count(9)') == '0'
        assert evalpy('[1,2,3,4,5,3].count(2)') == '1'
        assert evalpy('[1,2,3,4,5,3].count(3)') == '2'
        
        assert evalpy('a=[1,(2,3),4, (2,3), 5]; a.count((2,3))') == '2'
    
    def test_extend(self):
        assert evalpy('a=[1, 2]; b=[3, 4];a.extend(b); a') == '[ 1, 2, 3, 4 ]'
    
    def test_index(self):
        assert evalpy('[1,2,3,4,5,3].index(2)') == '1'
        assert evalpy('[1,2,3,4,5,3].index(3)') == '2'
        assert 'ValueError' in evalpy('try:\n  [1,2,3,4,5,3].index(9);\nexcept Exception as e:\n  e')
        assert evalpy('[1,2,3,4,5,3].index(3, 4)') == '5'
        assert evalpy('[1,2,3,4,5,3].index(3, -2)') == '5'
        assert evalpy('[1,2,3,4,5,3].index(3, 0, -2)') == '2'
        
        assert evalpy('a=[1,(2,3),4, (2,3), 5]; a.index((2,3))') == '1'
        assert evalpy('a=[1,(2,3),4, (2,3), 5]; a.index((2,3),2)') == '3'
    
    def test_insert(self):
        code = 'a=[1,2,3,4,5];'
        assert evalpy(code + 'a.insert(2, 9); a') == '[ 1, 2, 9, 3, 4, 5 ]'
        assert evalpy(code + 'a.insert(-1, 9); a') == '[ 1, 2, 3, 4, 9, 5 ]'
        assert evalpy(code + 'a.insert(99, 9); a') == '[ 1, 2, 3, 4, 5, 9 ]'
    
    def test_reverse(self):
        assert evalpy('a=[1,2,3,4,5]; a.reverse(); a') == '[ 5, 4, 3, 2, 1 ]'
        assert evalpy('a=[]; a.reverse(); a') == '[]'
    
    def test_sort(self):
        assert evalpy('a=[3,1,4,2]; a.sort(); a') == '[ 1, 2, 3, 4 ]'
        assert evalpy('a=[3,1,4,2]; a.sort(reverse=True); a') == '[ 4, 3, 2, 1 ]'
        assert evalpy('a=[3,1,4,2]; a.sort(key=lambda x: -x); a') == '[ 4, 3, 2, 1 ]'
        assert evalpy('a=[3,1,4,2]; a.sort(key=lambda x: -x, reverse=True); a') == '[ 1, 2, 3, 4 ]'
        
        assert evalpy('a=["bb", "aa", "mm", "dd"]; a.sort(); a') == "[ 'aa', 'bb', 'dd', 'mm' ]"
        assert evalpy('a=["bb", "aa", "mm", "dd"]; a.sort(key=lambda x: x); a') == "[ 'aa', 'bb', 'dd', 'mm' ]"
    
    def test_clear(self):
        assert evalpy('a=[3,1,4,2]; a.clear(); a') == '[]'
    
    def test_copy(self):
        assert evalpy('a=[3,1,4,2]; b = a.copy(); a.push(1); b') == '[ 3, 1, 4, 2 ]'
    
    def test_pop(self):
        code = 'a=[1,2,3,4,5];\n'
        assert evalpy(code + 'a.pop(2); a') == '[ 1, 2, 4, 5 ]'
        assert evalpy(code + 'a.pop(0); a') == '[ 2, 3, 4, 5 ]'
        assert evalpy(code + 'a.pop(); a') == '[ 1, 2, 3, 4 ]'
        assert evalpy(code + 'a.pop(-1); a') == '[ 1, 2, 3, 4 ]'
        assert 'IndexError' in evalpy(code + 'try:\n  a.pop(9);\nexcept Exception as e:\n  e')
    
    def test_no_list(self):
        code = 'class Foo:\n  def append(self): self.bar = 3\nfoo = Foo(); foo.append(2)\n'
        assert evalpy(code + 'foo.bar') == '3'
        code = 'class Foo:\n  def clear(self): self.bar = 3\nfoo = Foo(); foo.clear()\n'
        assert evalpy(code + 'foo.bar') == '3'
    
    def test_that_all_list_methods_are_tested(self):
        tested = set([x.split('_')[1] for x in dir(self) if x.startswith('test_')])
        needed = set([x for x in dir(list) if not x.startswith('_')])
        ignore = ''
        needed = needed.difference(ignore.split(' '))
        
        not_tested = needed.difference(tested)
        assert not not_tested


class TestDictMethods:
    
    def test_get(self):
        assert evalpy('a = {"foo":3}; a.get("foo")') == '3'
        assert evalpy('a = {"foo":3}; a.get("foo", 0)') == '3'
        assert evalpy('a = {"foo":3}; a.get("bar")') == 'null'
        assert evalpy('a = {"foo":3}; a.get("bar", 0)') == '0'
        # assert evalpy('{"foo":3}.get("foo")') == '3'
        # assert evalpy('{"foo":3}.get("bar", 0)') == '0'
    
    def test_items(self):
        assert nowhitespace(evalpy("d={'a':1, 'b':2, 3:3}; d.items()")) == "[['3',3],['a',1],['b',2]]"
        assert nowhitespace(evalpy("d={}; d.items()")) == "[]"
        
    def test_keys(self):
        assert nowhitespace(evalpy("d={'a':1, 'b':2, 3:3}; d.keys()")) == "['3','a','b']"
        assert nowhitespace(evalpy("d={}; d.keys()")) == "[]"
    
    def test_popitem(self):
        assert evalpy("d={'a': 1, 'b':2}; d.popitem()") == "[ 'a', 1 ]"
        assert 'KeyError' in evalpy("d={}\ntry:\n  d.popitem()\nexcept Exception as e:\n  e")
    
    def test_setdefault(self):
        assert evalpy("a = {}; a.setdefault('a', 7)") == '7'
        assert evalpy("a = {}; a.setdefault('a', 7); a.setdefault('a', 8)") == '7'
    
    def test_update(self):
        assert evalpy("a={}; b={'a':1, 'b':2}; a.update(b); a") == "{ a: 1, b: 2 }"
        assert evalpy("a={}; b={'a':1, 'b':2}; b.update(a); a") == "{}"
    
    def test_values(self):
        assert nowhitespace(evalpy("d={'a':1, 'b':2, 3:3};d.values()")) == "[3,1,2]"
        assert nowhitespace(evalpy("d={};d.values()")) == "[]"
    
    def test_clear(self):
        assert evalpy("a={'a':1, 'b':2}; a.clear(); a") == '{}'
        assert evalpy("a={}; a.clear(); a") == '{}'
    
    def test_copy(self):
        assert evalpy("a={'a':1, 'b':2}; b = a.copy(); b") == "{ a: 1, b: 2 }"
        assert evalpy("a={'a':1, 'b':2}; b = a.copy(); a['a']=9; b") == "{ a: 1, b: 2 }"
        assert evalpy("a={}; b = a.copy(); b") == "{}"
    
    def test_pop(self):
        assert evalpy("a={'a':1, 'b':2}; a.pop('a')") == '1'
        assert evalpy("a={'a':1, 'b':2}; a.pop('a', 9)") == '1'
        assert evalpy("a={'a':1, 'b':2}; a.pop('z', 9)") == '9'
        assert evalpy("a={'a':1, 'b':2}; a.pop('a'); a") == "{ b: 2 }"
    
    def test_no_dict(self):
        code = 'class Foo:\n  def get(self): return 42\n'
        assert evalpy(code + 'foo = Foo(); foo.get(1)') == '42'
        
        code = 'class Foo:\n  def clear(self): self.bar = 42\n'
        assert evalpy(code + 'foo = Foo(); foo.clear(); foo.bar') == '42'

    def test_that_all_dict_methods_are_tested(self):
        if sys.version_info[0] == 2:
            skip('On legacy py, the dict methods are different')
        tested = set([x.split('_')[1] for x in dir(self) if x.startswith('test_')])
        needed = set([x for x in dir(dict) if not x.startswith('_')])
        ignore = 'fromkeys'
        needed = needed.difference(ignore.split(' '))
        
        not_tested = needed.difference(tested)
        assert not not_tested


class TestStrMethods:
    
    def test_capitalize(self):
        assert evalpy('"".capitalize()') == ""
        assert evalpy('" _12".capitalize()') == " _12"
        assert evalpy('"_a".capitalize()') == "_a"
        assert evalpy('"foo bar".capitalize()') == "Foo bar"
        assert evalpy('"foo BAR".capitalize()') == "Foo bar"
    
    def test_title(self):
        assert evalpy('"".title()') == ""
        assert evalpy('" _12".title()') == " _12"
        assert evalpy('"_a".title()') == "_A"
        assert evalpy('"foo bar".title()') == "Foo Bar"
        assert evalpy('"foo BAR".title()') == "Foo Bar"
    
    def test_lower(self):
        assert evalpy('"".lower()') == ""
        assert evalpy('" _12".lower()') == " _12"
        assert evalpy('"foo bar".lower()') == "foo bar"
        assert evalpy('"foo BAR".lower()') == "foo bar"
    
    def test_upper(self):
        assert evalpy('"".upper()') == ""
        assert evalpy('" _12".upper()') == " _12"
        assert evalpy('"foo bar".upper()') == "FOO BAR"
        assert evalpy('"foo BAR".upper()') == "FOO BAR"
    
    def test_casefold(self):
        assert evalpy('"FoO bAr".casefold()') == "foo bar"
    
    def test_swapcase(self):
        assert evalpy('"".swapcase()') == ""
        assert evalpy('" _12".swapcase()') == " _12"
        assert evalpy('"foo bar".swapcase()') == "FOO BAR"
        assert evalpy('"foo BAR".swapcase()') == "FOO bar"
    
    def test_center(self):
        assert evalpy('"foo".center(5) + "."') == ' foo .'
        assert evalpy('"fo".center(5) + "."') == '  fo .'
        assert evalpy('"foo".center(1) + "."') == 'foo.'
        assert evalpy('"foo".center(5, "-")') == '-foo-'
    
    def test_ljust(self):
        assert evalpy('"foo".ljust(5) + "."') == 'foo  .'
        assert evalpy('"fo".ljust(5) + "."') == 'fo   .'
        assert evalpy('"foo".ljust(1) + "."') == 'foo.'
        assert evalpy('"foo".ljust(5, "-")') == 'foo--'
    
    def test_rjust(self):
        assert evalpy('"foo".rjust(5) + "."') == '  foo.'
        assert evalpy('"fo".rjust(5) + "."') == '   fo.'
        assert evalpy('"foo".rjust(1) + "."') == 'foo.'
        assert evalpy('"foo".rjust(5, "-")') == '--foo'
    
    def test_zfill(self):
        assert evalpy('"foo".zfill(5) + "."') == '00foo.'
        assert evalpy('"fo".zfill(5) + "."') == '000fo.'
        assert evalpy('"foo".zfill(1) + "."') == 'foo.'
    
    def test_count(self):
        assert evalpy('"foo".count("o")') == '2'
        assert evalpy('"foo".count("f")') == '1'
        assert evalpy('"foo".count("x")') == '0'
        assert evalpy('"foo".count("")') == '3'
        
        assert evalpy('"a--a--a".count("a")') == '3'
        assert evalpy('"a--a--a".count("a", 0)') == '3'
        assert evalpy('"a--a--a".count("a", 0, 99)') == '3'
        assert evalpy('"a--a--a".count("a", 1)') == '2'
        assert evalpy('"a--a--a".count("a", 0, 4)') == '2'
        assert evalpy('"a--a--a".count("a", 1, 4)') == '1'
        
    def test_endswith(self):
        assert evalpy('"blafoo".endswith("foo")') == 'true'
        assert evalpy('"blafoo".endswith("")') == 'true'
        assert evalpy('"foo".endswith("foo")') == 'true'
        assert evalpy('"".endswith("foo")') == 'false'
        assert evalpy('"".endswith("")') == 'true'
    
    def test_startswith(self):
        assert evalpy('"foobla".startswith("foo")') == 'true'
        assert evalpy('"foobla".startswith("")') == 'true'
        assert evalpy('"foo".startswith("foo")') == 'true'
        assert evalpy('"".startswith("foo")') == 'false'
        assert evalpy('"".startswith("")') == 'true'
        
        assert evalpy('("fo" + "obar").startswith("foo")') == "true"
    
    def test_expandtabs(self):
        assert evalpy('"a\tb\t\tc".expandtabs()') == 'a        b                c'
        assert evalpy('"a\tb\t\tc".expandtabs(2)') == 'a  b    c' 
    
    def test_find(self):
        assert evalpy('"abcdefgh".find("a")') == '0'
        assert evalpy('"abcdefgh".find("h")') == '7' 
        assert evalpy('"abcdefgh".find("z")') == '-1'
        assert evalpy('"abcdefgh".find("")') == '0'
        
        assert evalpy('"abcdefgh".find("cd")') == '2'
        assert evalpy('"abcdefgh".find("def")') == '3'
        
        assert evalpy('"ab ab ab".find("ab", 0)') == '0'
        assert evalpy('"ab ab ab".find("ab", 1)') == '3'
        assert evalpy('"ab ab ab".find("ab", -2)') == '6'
        assert evalpy('"     ab".find("ab", 0, 4)') == '-1'
        assert evalpy('"     ab".find("ab", 0, -1)') == '-1'
    
    def test_index(self):
        # We know that the implementation is basded on find; no need to test all
        assert evalpy('"abcdefgh".index("a")') == '0'
        assert evalpy('"abcdefgh".index("h")') == '7' 
        assert evalpy('"abcdefgh".index("")') == '0'
        assert 'ValueError' in evalpy('try:\n  "abcdefgh".index("z")\nexcept Exception as e:\n  e')
    
    def test_rfind(self):
        assert evalpy('"abcdefgh".rfind("a")') == '0'
        assert evalpy('"abcdefgh".rfind("h")') == '7' 
        assert evalpy('"abcdefgh".rfind("z")') == '-1'
        assert evalpy('"abcdefgh".rfind("")') == '8'
        
        assert evalpy('"abcdefgh".rfind("cd")') == '2'
        assert evalpy('"abcdefgh".rfind("def")') == '3'
        
        assert evalpy('"ab ab ab".rfind("ab", 0, -2)') == '3'
        assert evalpy('"ab ab ab".rfind("ab", 0, 3)') == '0'
        assert evalpy('"ab      ".rfind("ab", 3)') == '-1'
    
    def test_rindex(self):
        # We know that the implementation is basded on find; no need to test all
        assert evalpy('"abcdefghb".rindex("a")') == '0'
        assert evalpy('"abcdefghb".rindex("h")') == '7' 
        assert evalpy('"abcdefghb".rindex("")') == '9'
        assert evalpy('"abcdefghb".rindex("b")') == '8'
        assert 'ValueError' in evalpy('try:\n  "abcdefgh".rindex("z")\nexcept Exception as e:\n  e')
    
    def test_isalnum(self):
        assert evalpy('"".isalnum()') == 'false'
        assert evalpy('"012".isalnum()') == 'true'
        assert evalpy('"abc".isalnum()') == 'true'
        assert evalpy('"0a1b2c".isalnum()') == 'true'
        assert evalpy('"0a_".isalnum()') == 'false'
    
    def test_isalpha(self):
        assert evalpy('"".isalpha()') == 'false'
        assert evalpy('"012".isalpha()') == 'false'
        assert evalpy('"abc".isalpha()') == 'true'
        assert evalpy('"0a1b2c".isalpha()') == 'false'
        assert evalpy('"0a_".isalpha()') == 'false'
    
    def test_isnumeric(self):
        assert evalpy('"".isnumeric()') == 'false'
        assert evalpy('"012".isnumeric()') == 'true'
        assert evalpy('"abc".isnumeric()') == 'false'
        assert evalpy('"0a1b2c".isnumeric()') == 'false'
        assert evalpy('"0a_".isnumeric()') == 'false'
    
    def test_isidentifier(self):
        assert evalpy('"".isidentifier()') == 'false'
        assert evalpy('"012".isidentifier()') == 'false'
        assert evalpy('"abc".isidentifier()') == 'true'
        assert evalpy('"0a1b2c".isidentifier()') == 'false'
        assert evalpy('"a0a1b2c".isidentifier()') == 'true'
        assert evalpy('"0a_".isidentifier()') == 'false'
        assert evalpy('"_a".isidentifier()') == 'true'
        assert evalpy('"_0".isidentifier()') == 'true'
    
    def test_islower(self):
        assert evalpy('"".islower()') == 'false'
        assert evalpy('" ".islower()') == 'false'
        assert evalpy('"aBc".islower()') == 'false'
        assert evalpy('"aBc 01_".islower()') == 'false'
        
        assert evalpy('"abc".islower()') == 'true'
        assert evalpy('"abc 01_".islower()') == 'true'
    
    def test_isupper(self):
        assert evalpy('"".isupper()') == 'false'
        assert evalpy('" ".isupper()') == 'false'
        assert evalpy('"AbC".isupper()') == 'false'
        assert evalpy('"AbC 01_".isupper()') == 'false'
        
        assert evalpy('"ABC".isupper()') == 'true'
        assert evalpy('"ABC 01_".isupper()') == 'true'
    
    def test_isspace(self):
        assert evalpy('"".isspace()') == 'false'
        assert evalpy('" ".isspace()') == 'true'
        assert evalpy('" \\t\\n".isspace()') == 'true'
        assert evalpy('" _".isspace()') == 'false'
        assert evalpy('" a".isspace()') == 'false'
        assert evalpy('" 1".isspace()') == 'false'
    
    def test_istitle(self):
        assert evalpy('"".istitle()') == 'false'
        assert evalpy('" ".istitle()') == 'false'
        assert evalpy('"AbC".istitle()') == 'false'
        assert evalpy('"Foo bar".istitle()') == 'false'
        assert evalpy('"AbC 01_".istitle()') == 'false'
        
        assert evalpy('"Foo".istitle()') == 'true'
        assert evalpy('"Foo Bar".istitle()') == 'true'
        assert evalpy('"Foo 01_".istitle()') == 'true'
    
    def test_join(self):
        assert evalpy('"".join(["foo", "bar"])') == 'foobar'
        assert evalpy('" ".join(["foo", "bar"])') == 'foo bar'
        assert evalpy('"AA".join(["foo", "bar"])') == 'fooAAbar'
    
    def test_lstrip(self):
        assert evalpy('"".lstrip() + "."') == '.'
        assert evalpy('" \\t\\r\\n".lstrip() + "."') == '.'
        assert evalpy('"  ab x cd  ".lstrip() + "."') == 'ab x cd  .'
        assert evalpy('"  ab x cd  ".lstrip("x") + "."') == '  ab x cd  .'
        assert evalpy('"  ab x cd  ".lstrip(" x") + "."') == 'ab x cd  .'
        assert evalpy('"x x ab x cd x x".lstrip(" x") + "."') == 'ab x cd x x.'
    
    def test_rstrip(self):
        assert evalpy('"".rstrip() + "."') == '.'
        assert evalpy('" \\t\\r\\n".rstrip() + "."') == '.'
        assert evalpy('"  ab x cd  ".rstrip() + "."') == '  ab x cd.'
        assert evalpy('"  ab x cd  ".rstrip("x") + "."') == '  ab x cd  .'
        assert evalpy('"  ab x cd  ".rstrip(" x") + "."') == '  ab x cd.'
        assert evalpy('"x x ab x cd x x".rstrip(" x") + "."') == 'x x ab x cd.'
    
    def test_strip(self):
        assert evalpy('"".strip() + "."') == '.'
        assert evalpy('" \\t\\r\\n".strip() + "."') == '.'
        assert evalpy('"  ab x cd  ".strip() + "."') == 'ab x cd.'
        assert evalpy('"  ab x cd  ".strip("x") + "."') == '  ab x cd  .'
        assert evalpy('"  ab x cd  ".strip(" x") + "."') == 'ab x cd.'
        assert evalpy('"x x ab x cd x x".strip(" x") + "."') == 'ab x cd.'
    
    def test_partition(self):
        assert evalpy('"".partition("-")') == "[ '', '', '' ]"
        assert evalpy('"abc".partition("-")') == "[ 'abc', '', '' ]"
        assert evalpy('"-".partition("-")') == "[ '', '-', '' ]"
        assert evalpy('"abc-".partition("-")') == "[ 'abc', '-', '' ]"
        assert evalpy('"-def".partition("-")') == "[ '', '-', 'def' ]"
        assert evalpy('"abc-def".partition("-")') == "[ 'abc', '-', 'def' ]"
        
        assert 'ValueError' in evalpy('try:\n  "aa".partition("")\nexcept Exception as e:\n  e')
    
    def test_rpartition(self):
        assert evalpy('"".rpartition("-")') == "[ '', '', '' ]"
        assert evalpy('"abc".rpartition("-")') == "[ '', '', 'abc' ]"
        assert evalpy('"-".rpartition("-")') == "[ '', '-', '' ]"
        assert evalpy('"abc-".rpartition("-")') == "[ 'abc', '-', '' ]"
        assert evalpy('"-def".rpartition("-")') == "[ '', '-', 'def' ]"
        assert evalpy('"abc-def".rpartition("-")') == "[ 'abc', '-', 'def' ]"
    
    def test_split(self):
        assert evalpy('"".split("-")') == "[ '' ]"
        assert evalpy('"abc".split("-")') == "[ 'abc' ]"
        assert evalpy('"-".split("-")') == "[ '', '' ]"
        assert evalpy('"abc-".split("-")') == "[ 'abc', '' ]"
        assert evalpy('"-def".split("-")') == "[ '', 'def' ]"
        assert evalpy('"abc-def".split("-")') == "[ 'abc', 'def' ]"
        
        assert evalpy('"a a a".split(" ", 0)') == "[ 'a a a' ]"
        assert evalpy('"a a a".split(" ", 1)') == "[ 'a', 'a a' ]"
        assert evalpy('"a a a".split(" ", 2)') == "[ 'a', 'a', 'a' ]"
        assert evalpy('"a a a".split(" ", 3)') == "[ 'a', 'a', 'a' ]"
        assert evalpy('"a a a".split(" ", 99)') == "[ 'a', 'a', 'a' ]"
        
        assert evalpy('"a a\\ta\\na".split()') == "[ 'a', 'a', 'a', 'a' ]"
        assert 'ValueError' in evalpy('try:\n  "aa".split("")\nexcept Exception as e:\n  e')
    
    def test_rsplit(self):
        assert evalpy('"".rsplit("-")') == "[ '' ]"
        assert evalpy('"abc".rsplit("-")') == "[ 'abc' ]"
        assert evalpy('"-".rsplit("-")') == "[ '', '' ]"
        assert evalpy('"abc-".rsplit("-")') == "[ 'abc', '' ]"
        assert evalpy('"-def".rsplit("-")') == "[ '', 'def' ]"
        assert evalpy('"abc-def".rsplit("-")') == "[ 'abc', 'def' ]"
        
        assert evalpy('"a a a".rsplit(" ", 0)') == "[ 'a a a' ]"
        assert evalpy('"a a a".rsplit(" ", 1)') == "[ 'a a', 'a' ]"
        assert evalpy('"a a a".rsplit(" ", 2)') == "[ 'a', 'a', 'a' ]"
        assert evalpy('"a a a".rsplit(" ", 3)') == "[ 'a', 'a', 'a' ]"
        assert evalpy('"a a a".rsplit(" ", 99)') == "[ 'a', 'a', 'a' ]"
        
        assert evalpy('"a a\\ta\\na".split()') == "[ 'a', 'a', 'a', 'a' ]"
        assert 'ValueError' in evalpy('try:\n  "aa".split("")\nexcept Exception as e:\n  e')
    
    def test_splitlines(self):
        assert evalpy('"".splitlines()') == "[ '' ]"
        assert evalpy('"".splitlines(true)') == "[ '' ]"
        assert evalpy(r'"\n".splitlines()') == "[ '' ]"
        assert evalpy(r'"\n".splitlines(True)') == "[ '\\n' ]"
        
        assert evalpy(r'"abc def".splitlines()') == "[ 'abc def' ]"
        assert evalpy(r'"abc\ndef".splitlines()') == "[ 'abc', 'def' ]"
        assert evalpy(r'"abc\ndef\n".splitlines()') == "[ 'abc', 'def' ]"
        assert evalpy(r'"abc\rdef".splitlines()') == "[ 'abc', 'def' ]"
        assert evalpy(r'"abc\r\ndef".splitlines()') == "[ 'abc', 'def' ]"
        assert evalpy(r'"abc\n\rdef".splitlines()') == "[ 'abc', '', 'def' ]"
        
        assert evalpy(r'"abc def".splitlines(True)') == "[ 'abc def' ]"
        assert evalpy(r'"abc\ndef".splitlines(True)') == "[ 'abc\\n', 'def' ]"
        assert evalpy(r'"abc\ndef\n".splitlines(True)') == "[ 'abc\\n', 'def\\n' ]"
        assert evalpy(r'"abc\rdef".splitlines(True)') == "[ 'abc\\r', 'def' ]"
        assert evalpy(r'"abc\r\ndef".splitlines(True)') == "[ 'abc\\r\\n', 'def' ]"
        
        res = repr("X\n\nX\r\rX\r\n\rX\n\r\nX".splitlines(True)).replace(' ', '')
        res = res.replace('u"', '"').replace("u'", "'")  # arg legacy py
        assert nowhitespace(evalpy(r'"X\n\nX\r\rX\r\n\rX\n\r\nX".splitlines(true)')) == res
    
    def test_replace(self):
        assert evalpy("'abcABC'.replace('a', 'x')") == "xbcABC"
        assert evalpy("'abcABC'.replace('C', 'x')") == "abcABx"
        assert evalpy("'abcABC'.replace('cA', 'x')") == "abxBC"
        
        assert evalpy("'abababab'.replace('a', 'x', 0)") == "abababab"
        assert evalpy("'abababab'.replace('a', 'x', 1)") == "xbababab"
        assert evalpy("'abababab'.replace('a', 'x', 3)") == "xbxbxbab"
        assert evalpy("'abababab'.replace('a', 'x', 99)") == "xbxbxbxb"
        assert evalpy("'abababab'.replace('b', 'x', 2)") == "axaxabab"
    
    def test_translate(self):
        code = "table = {'a':'x', 'b':'y', 'c': None}\n"
        assert evalpy(code + "'abcde'.translate(table)") == "xyde"
    
    def test_that_all_str_methods_are_tested(self):
        tested = set([x.split('_')[1] for x in dir(self) if x.startswith('test_')])
        needed = set([x for x in dir(str) if not x.startswith('_')])
        ignore = 'encode decode format format_map isdecimal isdigit isprintable maketrans'
        needed = needed.difference(ignore.split(' '))
        
        not_tested = needed.difference(tested)
        assert not not_tested


run_tests_if_main()
