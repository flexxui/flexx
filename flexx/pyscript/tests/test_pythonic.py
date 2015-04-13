
from pytest import raises
from flexx.util.testing import run_tests_if_main

from flexx.pyscript import js, JSError, py2js, evaljs, evalpy


def nowhitespace(s):
    return s.replace('\n', '').replace('\t', '').replace(' ', '')


class TestBuildins:
    
    def test_max(self):
        assert py2js('max(3, 4)') == 'max(3, 4);'
    
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
    
    def test_len(self):
        assert py2js('len(a)') == 'a.length;'
        assert py2js('len(a, b)') == 'len(a, b);'


class TestListMethods:
    
    def test_append(self):
        assert nowhitespace(evalpy('a = [2]; a.append(3); a')) == '[2,3]'
    
    def test_remove(self):
        assert nowhitespace(evalpy('a = [2, 3]; a.remove(3); a')) == '[2]'
        assert nowhitespace(evalpy('a = [2, 3]; a.remove(2); a')) == '[3]'


run_tests_if_main()
