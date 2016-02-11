
from __future__ import print_function, absolute_import

import os
import sys
import bz2
import ast
import json
import time

from flexx.util.testing import run_tests_if_main, raises, skipif

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import commonast
#from flexx.pyscript import commonast


dirname = os.path.dirname(__file__)
filename1 = os.path.join(dirname, 'python_sample.py')
filename2 = os.path.join(dirname, 'python_sample2.py')
filename3 = os.path.join(dirname, 'python_sample3.py')


def _export_python_sample_ast():
    # Get what to export
    if sys.version_info > (3, ):
        filenames = filename1, filename3
    else:
        filenames = filename2,
    # Write
    for filename in filenames:
        filename_bz2 = filename[:-2] + 'bz2'
        code = open(filename, 'rb').read().decode()
        root = commonast.parse(code)
        ast_bin = bz2.compress(root.tojson(indent=None).encode())
        with open(filename_bz2, 'wb') as f:
            n = f.write(ast_bin) or 'some'
        print('wrote %s bytes to %s' % (n, filename_bz2))


def _get_ref_json(filename):
    filename_bz2 = filename[:-2] + 'bz2'
    js_ref = bz2.decompress(open(filename_bz2, 'rb').read()).decode()
    return json.dumps(json.loads(js_ref), indent=2, sort_keys=True)


def timeit(what, func, *args, **kwargs):
    t0 = time.perf_counter()
    func(*args, **kwargs)
    t1 = time.perf_counter()
    print('%s took %1.2f s' % (what, (t1-t0)))


def _performance_runner():
    """ Some simple perf tests ... 
    (this function's name should not include 'test')
    """
    code = open(filename1, 'rb').read().decode() * 100
    timeit('sample with ast.parse', ast.parse, code)
    timeit('sample with commonast.parse', commonast.parse, code)
    timeit('sample with commonast.parse + comments', commonast.parse, code, comments=True)
    
    code = """if x < 9:
    def foo(a, *b):
        # done
        return a + b or 4
    foo(3, 4*bar)
    """
    code = (code.strip() + '\n\n') * 10000
    
    print()
    timeit('minisample with ast.parse', ast.parse, code)
    timeit('minisample with commonast.parse', commonast.parse, code)
    timeit('minisample with commonast.parse + comments', commonast.parse, code, comments=True)


def test_Node_creation():
    
    Node = commonast.Node
    
    class MyNodeWithoutSlots(Node):
        pass
    
    class MyStubNode(Node):
        __slots__ = ()
    
    class MyNode(Node):
        __slots__ = 'name', 'op', 'foo_node', 'foo_nodes', 'bar'
    
    stubnode = MyStubNode()
    stubnodes = [MyStubNode(), MyStubNode(), MyStubNode()]
    
    # Node is an abstract class
    raises(AssertionError, Node)
    # Nodes must have slots (and no __dict__ to preserve memory)
    raises(AssertionError, MyNodeWithoutSlots)
    # number of names must match
    raises(AssertionError, MyNode, )
    raises(AssertionError, MyStubNode, 1)
    raises(AssertionError, MyNode, 'a', 'Add', stubnode, stubnodes, 1, 2)
    
    # These work
    node = MyNode('a', 'Add', stubnode, stubnodes, 1)
    node = MyNode('a', 'Add', None, stubnodes, 1)
    node = MyNode('a', 'Add', stubnode, [], 1)
    node = MyNode('a', 'Add', stubnode, stubnodes, 'bla')
    node = MyNode('a', 'Add', stubnode, stubnodes, [1, 2, 3])
    node = MyNode('a', 'Mult', stubnode, stubnodes, 1)
    node = MyNode('blas asdasd as', 'Mult', stubnode, stubnodes, 1)
    # Name must be a string
    raises(AssertionError, MyNode, 1, 'Add', stubnode, stubnodes, 1)
    # op must be an existing operator
    raises(AssertionError, MyNode, 'a', 'crap', stubnode, stubnodes, 1)
    # names ending with _node must be a node, and _nodes must be a list of nodes
    raises(AssertionError, MyNode, 'a', 'Add', 1, stubnodes, 1)
    raises(AssertionError, MyNode, 'a', 'Add', 'x', stubnodes, 1)
    raises(AssertionError, MyNode, 'a', 'Add', stubnode, 'not a node', 1)
    raises(AssertionError, MyNode, 'a', 'Add', stubnode, [1, 2], 1)
    # bar can be anything, but not a Node or list of Nodes
    raises(AssertionError, MyNode, 'a', 'Add', stubnode, stubnodes, stubnode)
    raises(AssertionError, MyNode, 'a', 'Add', stubnode, stubnodes, stubnodes)

def test_json_conversion():
    from commonast import Node, Assign, Name, BinOp, Bytes, Num
    
    # Test json conversion
    roota = Assign([Name('foo')], BinOp('Add', Name('a'), Num(3)))
    rootb = Assign([Name('foo')], BinOp('Add', None, Num(3.2)))
    rootc = Assign([Name('foo')], BinOp('Add', Bytes(b'xx'), Num(4j)))  
    
    for node1 in (roota, rootb, rootc):
        js = node1.tojson()
        node2 = Node.fromjson(js)
        #
        assert js.count('BinOp') == 1
        assert js.count('Num') == 1
        #
        assert node2.target_nodes[0].name == node1.target_nodes[0].name
        assert node2.value_node.op == node1.value_node.op
        assert node2.value_node.left_node == node1.value_node.left_node
        assert node2.value_node.right_node.value == node1.value_node.right_node.value
        # In fact, we can do
        node1 == node2
    
    assert roota != rootb
    assert roota != rootc
    with raises(ValueError):
        roota == 5
    
    assert str(roota) == roota.tojson()
    assert len(repr(roota)) < 80


def test_comments():
    code = """
    # cm0
    class Foo:
        # cm1
        def foo(self):
            # cm2
            if 1:
                # cm3
                a = 3
            else:
                # cm4
                a = 2
            for i in x:
                # cm5
                a += i
            else:
                # cm6
                pass
            while x:
                # cm7
                pass
            else:
                # cm8
                pass
            try:
                # cm9
                pass
            except Exception:
                # cm10
                pass
            else:
                # cm10
                pass
            finally:
                # cm11
                pass
            with foo:
               # cm12
               bar
    """
    code = '\n'.join(x[4:] for x in code.splitlines())
    
    root = commonast.parse(code, comments=False)
    assert 'cm' not in root.tojson()
    
    root = commonast.parse(code, comments=True)
    for i in range(13):
        assert ('cm%i' % i) in root.tojson()


def _compare_large_strings(text1, text2):
    # Compare in sections of 8 lines, with an overlap of 4,
    # to make fails easier to read. Invariant to newline-types in Str nodes.
    lines1, lines2 = text1.splitlines(), text2.splitlines()
    for i in range(0, max(len(lines1), len(lines2)), 4):
        prefix = '# line %i\n' % i
        sec1 = prefix + '\n'.join(lines1[i:i+8])
        sec2 = prefix + '\n'.join(lines2[i:i+8]).replace('\\r\\n', '\\n')  # for pypy
        assert sec1 == sec2


def test_compare_print():
    ast = commonast.parse('print(foo, bar)')
    n = ast.body_nodes[0].value_node
    assert isinstance(n, commonast.Call)
    assert n.func_node.name == 'print'
    assert len(n.arg_nodes) == 2
    assert n.arg_nodes[0].name == 'foo'
    assert n.arg_nodes[1].name == 'bar'


def test_consistent_ast():
    # Parse the sample file and export as a json string
    code = open(filename1, 'rb').read().decode()
    root = commonast.parse(code)
    js = root.tojson()
    # Compare with ref
    _compare_large_strings(_get_ref_json(filename1), js)


@skipif(sys.version_info > (3,), reason='not Python 2.x')
def test_consistent_ast2():
    # Parse the sample file and export as a json string
    code = open(filename2, 'rb').read().decode()
    root = commonast.parse(code)
    js = root.tojson()
    # Compare with ref
    _compare_large_strings(_get_ref_json(filename2), js)


@skipif(sys.version_info < (3,), reason='not Python 3.x')
def test_consistent_ast3():
    # Parse the sample file and export as a json string
    code = open(filename3, 'rb').read().decode()
    root = commonast.parse(code)
    js = root.tojson()
    # Compare with ref
    _compare_large_strings(_get_ref_json(filename3), js)


@skipif(sys.version_info < (3,), reason='not Python 3.x')
def test_functiondef_some_more():
    code = """
    def foo(a, b=3, *, c=4, d):
        pass
    def bar(a:[], b:(1,2), *c:'xx', **d:'yy') -> 'returns':
        pass
    """
    code = '\n'.join(x[4:] for x in code.splitlines())
    
    root = commonast.parse(code)
    assert len(root.body_nodes) == 2
    
    f1, f2 = root.body_nodes
    assert isinstance(f1, commonast.FunctionDef)
    assert isinstance(f2, commonast.FunctionDef)
    
    # Test args of foo (focus on default values)
    assert len(f1.arg_nodes) == 2
    assert len(f1.kwarg_nodes) == 2
    for arg, name in zip(f1.arg_nodes + f1.kwarg_nodes, 'abcd'):
        assert isinstance(arg, commonast.Arg)
        assert arg.name == name
        assert arg.annotation_node is None
    assert f1.arg_nodes[0].value_node is None
    assert f1.arg_nodes[1].value_node.value == 3  # Num node
    assert f1.kwarg_nodes[0].value_node.value == 4
    assert f1.kwarg_nodes[1].value_node is None
    
    # Test args of bar (focus on annotations)
    assert len(f2.arg_nodes) == 2
    assert len(f2.kwarg_nodes) == 0
    for arg, name in zip(f2.arg_nodes + [f2.args_node, f2.kwargs_node], 'abcd'):
        assert isinstance(arg, commonast.Arg)
        assert arg.name == name
    assert f2.args_node.value_node is None
    assert f2.kwargs_node.value_node is None
    #
    assert isinstance(f2.arg_nodes[0].annotation_node, commonast.List)
    assert isinstance(f2.arg_nodes[1].annotation_node, commonast.Tuple)
    assert isinstance(f2.args_node.annotation_node, commonast.Str)
    assert isinstance(f2.kwargs_node.annotation_node, commonast.Str)


def test_call_some_more():
    from commonast import Name, Num, Starred, Keyword
    
    code = "foo(1, a, *b, c=3, **d)"
    node = commonast.parse(code).body_nodes[0].value_node  # Call is in an Expr
    assert isinstance(node, commonast.Call)
    
    assert len(node.arg_nodes) == 3
    assert len(node.kwarg_nodes) == 2
    for arg, cls in zip(node.arg_nodes + node.kwarg_nodes,
                   [Num, Name, Starred, Num, None.__class__]):
        isinstance(arg, cls)
    assert node.arg_nodes[2].value_node.name == 'b'
    assert node.kwarg_nodes[1].name is None
    assert node.kwarg_nodes[1].value_node.name == 'd' # keyword with emtpy name


@skipif(sys.version_info < (3,5), reason='Need Python 3.5+')
def test_call_even_some_more():
    from commonast import Name, Num, Starred, Keyword
    
    code = "foo(a, *b, c, *d, **e, **f)"
    node = commonast.parse(code).body_nodes[0].value_node
    
    assert len(node.arg_nodes) == 4
    assert len(node.kwarg_nodes) == 2
    for arg, cls in zip(node.arg_nodes + node.kwarg_nodes,
                   [Name, Starred, Name, Starred, Keyword, Keyword]):
        isinstance(arg, cls)
    

@skipif(sys.version_info < (3,), reason='not Python 3.x')
def test_classdef_some_more():
    code = "class Foo(Bar, *bases, metaclass=X, **extra_kwargs): pass"
    node = commonast.parse(code).body_nodes[0]
    assert isinstance(node, commonast.ClassDef)
    
    assert len(node.arg_nodes) == 2
    assert len(node.kwarg_nodes) == 2
    #
    assert node.arg_nodes[0].name == 'Bar'
    assert isinstance(node.arg_nodes[1], commonast.Starred)
    assert node.arg_nodes[1].value_node.name == 'bases'
    # kwarg nodes are Keywords
    assert node.kwarg_nodes[0].name == 'metaclass'
    assert node.kwarg_nodes[0].value_node.name == 'X'  # Name node
    assert node.kwarg_nodes[1].name is None 
    assert node.kwarg_nodes[1].value_node.name == 'extra_kwargs'


@skipif(sys.version_info > (3,), reason='not Python 2.x')
def test_python2_old_syntax():
    # We do not support tuple function arg; it would complicate things
    with raises(RuntimeError):
        commonast.parse('def foo((a,)=c):pass')
    # Print statement becomes print function
    assert commonast.parse('print(foo)') == commonast.parse('print foo')
    # Exec statement becomes a d function
    assert commonast.parse('exec(foo)') == commonast.parse('exec foo')
    # Backticks becomes repr function
    assert commonast.parse('repr(foo)') == commonast.parse('`foo`')


@skipif(sys.version_info < (3,3), reason='Need Python 3.3+')
def test_python_33_plus():
    
    # Yield from
    code = "def foo():\n   yield from x"
    root = commonast.parse(code).body_nodes[0]
    node = root.body_nodes[0].value_node
    assert isinstance(node, commonast.YieldFrom)


run_tests_if_main()
