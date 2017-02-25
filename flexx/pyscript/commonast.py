"""
Module that defines a common AST description, independent from Python
version and implementation. Also provides a function ``parse()`` to
generate this common AST by using the buildin ast module and converting
the result. Supports CPython 2.7, CPython 3.2+, Pypy.

https://github.com/almarklein/commonast
"""

# Notes:
# Python 3.6 introduced ast.Constant, which seems to be added so that 3d
# party code can use it, but ast.parse does not produce it afaik.

from __future__ import print_function, absolute_import

import sys
import ast
import json
from base64 import encodestring as encodebytes, decodestring as decodebytes

pyversion = sys.version_info
NoneType = None.__class__

if pyversion >= (3, ):
    basestring = str  # noqa


# do some extra asserts when running tests, but not always, for speed
docheck = 'pytest' in sys.modules

def parse(code, comments=False):
    """ Parse Python code to produce a common AST tree.
    
    Parameters:
        code (str): the Python code to parse
        comments (bool): if True, will include Comment nodes. Default False.
    """
    converter = NativeAstConverter(code)
    return converter.convert(comments)


class Node(object):
    """ Abstract base class for all Nodes.
    """
    
    __slots__ = ['lineno', 'col_offset']
    
    class OPS:
        """ Operator enums: """
        # Unary
        UAdd = 'UAdd'
        USub = 'USub'
        Not = 'Not'
        Invert = 'Invert'
        # Binary
        Add = 'Add'
        Sub = 'Sub'
        Mult = 'Mult'
        Div = 'Div'
        FloorDiv = 'FloorDiv'
        Mod = 'Mod'
        Pow = 'Pow'
        LShift = 'LShift'
        RShift = 'RShift'
        BitOr = 'BitOr'
        BitXor = 'BitXor'
        BitAnd = 'BitAnd'
        # Boolean
        And = 'And'
        Or = 'Or'
    
    class COMP:
        """ Comparison enums: """
        Eq = 'Eq'
        NotEq = 'NotEq'
        Lt = 'Lt'
        LtE = 'LtE'
        Gt = 'Gt'
        GtE = 'GtE'
        Is = 'Is'
        IsNot = 'IsNot'
        In = 'In'
        NotIn = 'NotIn'
    
    def __init__(self, *args):
        names = self.__slots__
        # Checks
        assert len(args) == len(names)  # check this always
        if docheck:
            assert not hasattr(self, '__dict__'), 'Nodes must have __slots__'
            assert self.__class__ is not Node, 'Node is an abstract class'
            for name, val in zip(names, args):
                assert not isinstance(val, ast.AST)
                if name == 'name':
                    assert isinstance(val, (basestring, NoneType)), 'name not a string'
                elif name == 'op':
                    assert val in Node.OPS.__dict__ or val in Node.COMP.__dict__
                elif name.endswith('_node'):
                    assert isinstance(val, (Node, NoneType)), '%r is not a Node' % name
                elif name.endswith('_nodes'):
                    islistofnodes = (isinstance(val, list) and 
                                     all(isinstance(n, Node) for n in val))
                    assert islistofnodes, '%r is not a list of nodes' % name
                else:
                    assert not isinstance(val, Node), '%r should not be a Node' % name
                    assert not (isinstance(val, list) and 
                                all(isinstance(n, Node) for n in val))
        # Assign
        for name, val in zip(names, args):
            setattr(self, name, val)
    
    def tojson(self, indent=2):
        """ Return a string with the JSON representatiom of this AST.
        Set indent to None for a more compact representation.
        """
        return json.dumps(self._todict(), indent=indent, sort_keys=True)
    
    @classmethod
    def fromjson(cls, text):
        """ Classmethod to create an AST tree from JSON.
        """
        return Node._fromdict(json.loads(text))
        
    @classmethod
    def _fromdict(cls, d):
        assert '_type' in d
        Cls = globals()[d['_type']]
        
        args = []
        for name in Cls.__slots__:
            val = d[name]
            if val is None:
                pass
            elif name.endswith('_node'):
                val = Node._fromdict(val)
            elif name.endswith('_nodes'):
                val = [Node._fromdict(x) for x in val]
            elif isinstance(val, basestring):
                if val.startswith('BYTES:'):
                    val = decodebytes(val[6:].encode('utf-8'))
                elif val.startswith('COMPLEX:'):
                    val = complex(val[8:])
                elif pyversion < (3, ):
                    val = unicode(val)  # noqa
            args.append(val)
        return Cls(*args)
    
    def _todict(self):
        """ Get a dict representing this AST. This is the basis for
        creating JSON, but can be used to compare AST trees as well.
        """
        d = {}
        d['_type'] = self.__class__.__name__
        for name in self.__slots__:
            val = getattr(self, name)
            if val is None:
                pass
            elif name.endswith('_node'):
                val = val._todict()
            elif name.endswith('_nodes'):
                val = [x._todict() for x in val]
            elif isinstance(self, Bytes) and isinstance(val, bytes):
                val = 'BYTES:' + encodebytes(val).decode('utf-8').rstrip()
            elif isinstance(self, Num) and isinstance(val, complex):
                val = 'COMPLEX:' + repr(val)
            d[name] = val
        return d
    
    def __eq__(self, other):
        if not isinstance(other, Node):
            raise ValueError('Can only compare nodes to other nodes.')
        return self._todict() == other._todict()
    
    def __repr__(self):
        names = ', '.join([repr(x) for x in self.__slots__])
        return '<%s with %s at 0x%x>' % (self.__class__.__name__, names, id(self))
    
    def __str__(self):
        return self.tojson()


try:
    Node.OPS.__doc__ += ', '.join([x for x in sorted(Node.OPS.__dict__)
                                   if not x.startswith('_')])
    Node.COMP.__doc__ += ', '.join([x for x in sorted(Node.COMP.__dict__)
                                    if not x.startswith('_')])
except AttributeError:  # pragma: no cover
    pass  # Py < 3.3


## -- (start marker for doc generator)

## General

class Comment(Node):
    """
    Attributes:
        value: the comment string.
    """
    __slots__ = 'value',

class Module(Node):
    """ Each code that an AST is created for gets wrapped in a Module node.
    
    Attributes:
        body_nodes: a list of nodes.
    """
    __slots__ = 'body_nodes',

## Literals

class Num(Node):
    """
    Attributes:
        value: the number as a native Python object (int, float, or complex).
    """
    __slots__ = 'value',

class Str(Node):
    """
    Attributes:
        value: the native Python str object.
    """
    __slots__ = 'value',

class Bytes(Node):
    """
    Attributes:
        value: the native Python bytes object.
    """
    __slots__ = 'value',

class List(Node):
    """
    Attributes:
        element_nodes: the items in the list.
    """
    __slots__ = 'element_nodes',

class Tuple(Node):
    """
    Attributes:
        element_nodes: the items in the tuple.
    """
    __slots__ = 'element_nodes',

class Set(Node):
    """
    Attributes:
        element_nodes: the items in the set.
    """
    __slots__ = 'element_nodes',

class Dict(Node):
    """
    Attributes:
        key_nodes: the keys of the dict.
        value_nodes: the corresponding values.
    """
    __slots__ = 'key_nodes', 'value_nodes'

class Ellipsis(Node):
    """ Represents the ``...`` syntax for the Ellipsis singleton.
    """
    __slots__ = ()

class NameConstant(Node):
    """
    Attributes:
        value: the corresponding native Python object like True, False or None.
    """
    __slots__ = 'value',

## Variables, attributes, indexing and slicing

class Name(Node):
    """
    Attributes:
        name: the string name of this variable.
    """
    __slots__ = 'name',

class Starred(Node):
    """ A starred variable name, e.g. ``*foo``. Note that this isn't
    used to define a function with ``*args`` - FunctionDef nodes have
    special fields for that.
    
    Attributes:
        value_node: the value that is starred, typically a Name node.
    """
    __slots__ = 'value_node',

class Attribute(Node):
    """ Attribute access, e.g. ``foo.bar``.
    
    Attributes:
        value_node: The node to get/set an attribute of. Typically a Name node.
        attr: a string with the name of the attribute.
    """
    __slots__ = 'value_node', 'attr'

class Subscript(Node):
    """ Subscript access, e.g. ``foo[3]``.
    
    Attributes:
        value_node: The node to get/set a subscript of. Typically a Name node.
        slice_node: An Index, Slice or ExtSlice node.
    """
    __slots__ = 'value_node', 'slice_node'

class Index(Node):
    """
    Attributes:
        value_node: Single index.
    """
    __slots__ = 'value_node',

class Slice(Node):
    """
    Attributes:
        lower_node: start slice.
        upper_node: end slice.
        step_node: slice step.
    """
    __slots__ = 'lower_node', 'upper_node', 'step_node'

class ExtSlice(Node):
    """
    Attributes:
        dim_nodes: list of Index and Slice nodes (of for each dimension).
    """
    __slots__ = 'dim_nodes',

## Expressions

class Expr(Node):
    """ When an expression, such as a function call, appears as a
    statement by itself (an expression statement), with its return value
    not used or stored, it is wrapped in this container.
    
    Attributes:
        value_node: holds one of the other nodes in this section, or a
            literal, a Name, a Lambda, or a Yield or YieldFrom node.
    """
    __slots__ = 'value_node',

class UnaryOp(Node):
    """ A unary operation (e.g. ``-x``, ``not x``).
    
    Attributes:
        op: the operator (an enum from ``Node.OPS``).
        right_node: the operand at the right of the operator.
    """
    __slots__ = 'op', 'right_node'

class BinOp(Node):
    """ A binary operation (e.g. ``a / b``, ``a + b``).
    
    Attributes:
        op: the operator (an enum from ``Node.OPS``).
        left_node: the node to the left of the operator.
        right_node: the node to the right of the operator.
    """
    __slots__ = 'op', 'left_node', 'right_node'

class BoolOp(Node):
    """ A boolean operator (``and``, ``or``, but not ``not``).
    
    Attributes:
        op: the operator (an enum from ``Node.OPS``).
        value_nodes: a list of nodes. ``a``, ``b`` and ``c`` in 
            ``a or b or c``.
    """
    __slots__ = 'op', 'value_nodes'

class Compare(Node):
    """ A comparison of two or more values. 
    
    Attributes:
        op: the comparison operator (an enum from ``Node.COMP``).
        left_node: the node to the left of the operator.
        right_node: the node to the right of the operator.
    """
    __slots__ = 'op', 'left_node', 'right_node'

class Call(Node):
    """ A function call.
    
    Attributes:
        func_node: Name, Attribute or SubScript node that represents
            the function.
        arg_nodes: list of nodes representing positional arguments.
        kwarg_nodes: list of Keyword nodes representing keyword arguments.
    
    Note that an argument ``*x`` would be specified as a Starred node
    in arg_nodes, and ``**y`` as a Keyword node with a name being ``None``.
    """
    __slots__ = ('func_node', 'arg_nodes', 'kwarg_nodes')

class Keyword(Node):
    """ Keyword argument used in a Call.
    
    Attributes:
        name: the (string) name of the argument. Is None for ``**kwargs``.
        value_node: the value of the arg. 
    """
    __slots__ = ('name', 'value_node')

class IfExp(Node):
    """ An expression such as ``a if b else c``.
    
    Attributes:
        test_node: the ``b`` in the above.
        body_node: the ``a`` in the above.
        else_node: the ``c`` in the above.
    """
    __slots__ = 'test_node', 'body_node', 'else_node'

class ListComp(Node):
    """ List comprehension.
    
    Attributes:
        element_node: the part being evaluated for each item.
        comp_nodes: a list of Comprehension nodes.
    """
    __slots__ = 'element_node', 'comp_nodes'

class SetComp(Node):
    """ Set comprehension. See ListComp.
    """
    __slots__ = 'element_node', 'comp_nodes'

class GeneratorExp(Node):
    """ Generor expression. See ListComp.
    """
    __slots__ = 'element_node', 'comp_nodes'

class DictComp(Node):
    """ Dict comprehension.
    
    Attributes:
        key_node: the key of the item being evaluated.
        value_node: the value of the item being evaluated.
        comp_nodes: a list of Comprehension nodes.
    """
    __slots__ = 'key_node', 'value_node', 'comp_nodes'

class Comprehension(Node):
    """ Represents a single for-clause in a comprehension.
    
    Attributes:
        target_node: reference to use for each element, typically a
            Name or Tuple node.
        iter_node: the object to iterate over.
        if_nodes: a list of test expressions.
    """
    __slots__ = 'target_node', 'iter_node', 'if_nodes'


## Statements

class Assign(Node):
    """ Assignment of a value to a variable.
    
    Attributes:
        target_nodes: variables to assign to, Name or SubScript.
        value_node: the object to assign.
    """
    __slots__ = 'target_nodes', 'value_node'

class AugAssign(Node):
    """ Augmented assignment, such as ``a += 1``.
    
    Attributes:
        target_node: variable to assign to, Name or SubScript.
        op: operator enum (e.g. ``Node.OPS.Add``)
        value_node: the object to assign.
    """ 
    __slots__ = 'target_node', 'op', 'value_node'


class Raise(Node):
    """ Raising an exception.
    
    Attributes:
        exc_node: the exception object to be raised, normally a Call
            or Name, or None for a standalone raise.
        cause_node: the optional part for y in raise x from y.
    """
    __slots__ = 'exc_node', 'cause_node'

class Assert(Node):
    """ An assertion.
    
    Attributes:
        test_node: the condition to test.
        msg_node: the failure message (commonly a Str node)
    """
    __slots__ = 'test_node', 'msg_node'

class Delete(Node):
    """ A del statement.
    
    Attributes:
        target_nodes: the variables to delete, such as Name, Attribute
            or Subscript nodes.
    """
    __slots__ = 'target_nodes',

class Pass(Node):
    """ Do nothing.
    """
    __slots__ = ()

class Import(Node):
    """ An import statement.
    
    Attributes:
        root: the name of the module to import from. None if this is
            not a from-import.
        names: list of (name, alias) tuples, where alias can be None.
        level: an integer indicating depth of import. Zero means
            absolute import.
    """
    __slots__ = 'root', 'names', 'level'

## Control flow

class If(Node):
    """ An if-statement.
    
    Note that elif clauses don't have a special representation in the
    AST, but rather appear as extra If nodes within the else section
    of the previous one.
    
    Attributes:
        test_node: the test, e.g. a Compare node.
        body_nodes: the body of the if-statement.
        else_nodes: the body of the else-clause of the if-statement.
    """
    __slots__ = 'test_node', 'body_nodes', 'else_nodes'

class For(Node):
    """ A for-loop.
    
    Attributes:
        target_node: the variable(s) the loop assigns to.
        iter_node: the object to iterate over.
        body_nodes: the body of the for-loop.
        else_nodes: the body of the else-clause of the for-loop.
    """
    __slots__ = 'target_node', 'iter_node', 'body_nodes', 'else_nodes'

class While(Node):
    """ A while-loop.
    
    Attributes:
        test_node: the test to perform on each iteration.
        body_nodes: the body of the for-loop.
        else_nodes: the body of the else-clause of the for-loop.
    """
    __slots__ = 'test_node', 'body_nodes', 'else_nodes'

class Break(Node):
    """ Break from a loop.
    """
    __slots__ = ()

class Continue(Node):
    """ Continue with next iteration of a loop.
    """
    __slots__ = ()

class Try(Node):
    """ Try-block.
    
    Attributes:
        body_nodes: the body of the try-block (i.e. the code to try).
        handler_nodes: a list of ExceptHandler instances.
        else_nodes: the body of the else-clause of the try-block.
        finally_nodes: the body of the finally-clause of the try-block.
    """
    __slots__ = 'body_nodes', 'handler_nodes', 'else_nodes', 'finally_nodes'

class ExceptHandler(Node):
    """ Single except-clause.
    
    Attributes:
        type_node: the type of exception to catch. Often a Name node
            or None to catch all.
        name: the string name of the exception object in case of ``as err``.
            None otherwise.
        body_nodes: the body of the except-clause.
    """
    __slots__ = 'type_node', 'name', 'body_nodes'

class With(Node):
    """ A with-block (i.e. a context manager).
    
    Attributes:
        item_nodes: a list of WithItem nodes (i.e. context managers).
        body_nodes: the body of the with-block.
    """
    __slots__ = 'item_nodes', 'body_nodes'

class WithItem(Node):
    """ A single context manager in a with block.
    
    Attributes:
        expr_node: the expression for the context manager.
        as_node: a Name, Tuple or List node representing the ``as foo`` part.
    """
    __slots__ = 'expr_node', 'as_node'

## Function and class definitions

class FunctionDef(Node):
    """ A function definition.
    
    Attributes:
        name: the (string) name of the function.
        decorator_nodes: the list of decorators to be applied, stored
            outermost first (i.e. the first in the list will be applied
            last).
        annotation_node: the return annotation (Python 3 only).
        arg_nodes: list of Args nodes representing positional arguments.
            These *may* have a default value.
        kwarg_nodes: list of Arg nodes representing keyword-only arguments.
        args_node: an Arg node representing ``*args``.
        kwargs_node: an Arg node representing ``**kwargs``.
        body_nodes: the body of the function.
    """
    __slots__ = ('name', 'decorator_nodes', 'annotation_node',
                 'arg_nodes', 'kwarg_nodes', 'args_node', 'kwargs_node', 
                 'body_nodes')

class Lambda(Node):
    """ Anonymous function definition.
    
    Attributes:
        arg_nodes: list of Args nodes representing positional arguments.
        kwarg_nodes: list of Arg nodes representing keyword-only arguments.
        args_node: an Arg node representing ``*args``.
        kwargs_node: an Arg node representing ``**kwargs``.
        body_node: the body of the function (a single node).
    """
    __slots__ = ('arg_nodes', 'kwarg_nodes', 'args_node', 'kwargs_node', 
                 'body_node')
    
class Arg(Node):
    """ Function argument for a FunctionDef.
    
    Attributes:
        name: the (string) name of the argument.
        value_node: the default value of this argument. Can be None.
        annotation_node: the annotation for this argument (Python3 only).
    """
    
    __slots__ = ('name', 'value_node', 'annotation_node')

class Return(Node):
    """
    Attributes:
        value_node: the value to return.
    """
    __slots__ = 'value_node',

class Yield(Node):
    """
    Attributes:
        value_node: the value to yield.
    """
    __slots__ = 'value_node',

class YieldFrom(Node):
    """
    Attributes:
        value_node: the value to yield.
    """
    __slots__ = 'value_node',

class Global(Node):
    """
    Attributes:
        names: a list of string names to declare global.
    """
    __slots__ = 'names',

class Nonlocal(Node):
    """
    Attributes:
        names: a list of string names to declare nonlocal.
    """
    __slots__ = 'names',

class ClassDef(Node):
    """ A class definition.
    
    Attributes:
        name: a string for the class name.
        decorator_nodes: the list of decorators to be applied, as in FunctionDef.
        arg_nodes: list of nodes representing base classes.
        kwarg_nodes: list of Keyword nodes representing keyword-only arguments.
        body_nodes: the body of the class.
    
    Note that arg_nodes and kwarg_nodes are similar to those in the
    Call node. An argument ``*x`` would be specified as a Starred node
    in arg_nodes, and ``**y`` as a Keyword node with a name being
    ``None``. For more information on keyword arguments see
    https://www.python.org/dev/peps/pep-3115/.
    """
    __slots__ = ('name', 'decorator_nodes', 'arg_nodes', 'kwarg_nodes', 'body_nodes')

## -- (end marker for doc generator)


class NativeAstConverter:
    """ Convert ast produced by Python's ast module to common ast.
    """
    
    def __init__(self, code):
        self._root = ast.parse(code)
        self._lines =code.splitlines()
        self._stack = []  # contains tuple elements: (list_obj, native_nodes)
    
    def _add_comments(self, container, lineno):
        """ Add comment nodes from the last point until the given line number.
        """
        linenr1 = self._comment_pointer
        linenr2 = lineno
        self._comment_pointer = linenr2 + 1  # store for next time
        
        for i in range(linenr1, linenr2):
            line = self._lines[i-1]  # lineno's start from 1
            if line.lstrip().startswith('#'):
                before, _, comment = line.partition('#')
                node = Comment(comment)
                node.lineno = i
                node.col_offset = len(before)
                container.append(node)
    
    def convert(self, comments=False):
        assert not self._stack
        self._comment_pointer = 1
        
        result = self._convert(self._root)
        
        while self._stack:
            container, native_nodes = self._stack.pop(0)
            for native_node in native_nodes:
                node = self._convert(native_node)
                if comments:
                    self._add_comments(container, node.lineno)
                container.append(node)
        
        return result
    
    def _convert(self, n):
        
        # n is the native node produced by the ast module
        if n is None:
            return None  # but some node attributes can be None
        assert isinstance(n, ast.AST)
        
        # Get converter function
        type = n.__class__.__name__
        try:
            converter = getattr(self, '_convert_' + type)
        except AttributeError:  # pragma: no cover
            raise RuntimeError('Cannot convert %s nodes.' % type)
        # Convert node
        val = converter(n)
        assert isinstance(val, Node)
        # Set its position
        val.lineno = getattr(n, 'lineno', 1)
        val.col_offset = getattr(n, 'col_offset', 0)
        return val
    
    def _convert_Module(self, n):
        node = Module([])
        self._stack.append((node.body_nodes, n.body))
        return node
    
    ## Literals
    
    def _convert_Num(self, n):
        if pyversion < (3, ) and str(n.n).startswith('-'):
            # -4 is a unary sub on 4, dont forget complex numbers
            return UnaryOp(Node.OPS.USub, Num(-n.n))
        return Num(n.n)
    
    def _convert_Str(self, n):
        # Get string modifier char
        line = self._lines[n.lineno-1]
        pre = ''
        if line[n.col_offset] not in '"\'':
            pre += line[n.col_offset]
            if line[n.col_offset + 1] not in '"\'':
                pre += line[n.col_offset + 1]
        # Formatted, bytes?
        if 'f' in pre:
            raise RuntimeError('Cannot do formatted string literals yet: ' +
                               line)
        if pyversion < (3, ) and 'b' in pre:
            return Bytes(n.s)
        return Str(n.s)
    
    def _convert_Bytes(self, n):
        return Bytes(n.s)
    
    def _convert_List(self, n):
        c = self._convert
        return List([c(x) for x in n.elts])
    
    def _convert_Tuple(self, n):
        c = self._convert
        return Tuple([c(x) for x in n.elts])
    
    def _convert_Set(self, n):
        c = self._convert
        return Set([c(x) for x in n.elts])
    
    def _convert_Dict(self, n):
        c = self._convert
        return Dict([c(x) for x in n.keys], [c(x) for x in n.values])
    
    def _convert_Ellipsis(self, n):
        if pyversion < (3, ):
            return Index(Ellipsis())  # Ellipses must be wrapped in an index
        return Ellipsis()
    
    def _convert_NameConstant(self, n):
        return NameConstant(n.value)
    
    ## Variables, attributes, indexing and slicing
    
    def _convert_Name(self, n):
        if pyversion < (3, 4):  # pragma: no cover
            M = {'None': None, 'False': False, 'True': True}
            if n.id in M:
                return NameConstant(M[n.id])  # Python < 3.4
        if pyversion < (3, ) and isinstance(n.ctx , ast.Param):
            return Arg(n.id, None, None)
        return Name(n.id)
    
    def _convert_Starred(self, n):
        return Starred(self._convert(n.value))
    
    def _convert_Attribute(self, n):
        return Attribute(self._convert(n.value), n.attr)
    
    def _convert_Subscript(self, n):
        return Subscript(self._convert(n.value), self._convert(n.slice))
    
    def _convert_Index(self, n):
        return Index(self._convert(n.value))
    
    def _convert_Slice(self, n):
        c = self._convert
        step = c(n.step)
        if pyversion < (3, ) and isinstance(step, NameConstant) and step.value is None:
            if not self._lines[n.step.lineno-1][n.step.col_offset:].startswith('None'):
                step = None  # silly Python 2 turns a[::] into a[::None]
        return Slice(c(n.lower), c(n.upper), step)
    
    def _convert_ExtSlice(self, n):
        c = self._convert
        return ExtSlice([c(x) for x in n.dims])
    
    ## Expressions
    
    def _convert_Expr(self, n):
        return Expr(self._convert(n.value))
    
    def _convert_UnaryOp(self, n):
        op = n.op.__class__.__name__
        return UnaryOp(op, self._convert(n.operand))
    
    def _convert_BinOp(self, n):
        op = n.op.__class__.__name__
        return BinOp(op, self._convert(n.left), self._convert(n.right))
    
    def _convert_BoolOp(self, n):
        c = self._convert
        op = n.op.__class__.__name__
        return BoolOp(op, [c(x) for x in n.values])  # list of value_nodes
    
    def _convert_Compare(self, n):
        c = self._convert
        # Get compares and ops
        comps = [c(x) for x in ([n.left] + n.comparators)]
        ops = [op.__class__.__name__ for op in n.ops]
        assert len(ops) == (len(comps) - 1)
        # Create our comparison operators
        compares = []
        for i in range(len(ops)):
            co = Compare(ops[i], comps[i], comps[i+1])
            compares.append(co)
        # Return single or wrapped in an AND
        assert compares
        if len(compares) == 1:
            return compares[0]
        else:
            return BoolOp(Node.OPS.And, compares)
    
    def _convert_Call(self, n):
        c = self._convert
        arg_nodes = [c(a) for a in n.args]
        kwarg_nodes = [c(a) for a in n.keywords]
        
        if pyversion < (3, 5):
            if n.starargs:
                arg_nodes.append(Starred(c(n.starargs)))
            if n.kwargs:
                kwarg_nodes.append(Keyword(None, c(n.kwargs)))
        
        return Call(c(n.func), arg_nodes, kwarg_nodes)
    
    def _convert_keyword(self, n):
        return Keyword(n.arg, self._convert(n.value or None))
    
    def _convert_IfExp(self, n):
        c = self._convert
        return IfExp(c(n.test), c(n.body), c(n.orelse))
    
    def _convert_ListComp(self, n):
        c = self._convert
        return ListComp(c(n.elt), [c(x) for x in n.generators])
    
    def _convert_SetComp(self, n):
        c = self._convert
        return SetComp(c(n.elt), [c(x) for x in n.generators])
    
    def _convert_GeneratorExp(self, n):
        c = self._convert
        return GeneratorExp(c(n.elt), [c(x) for x in n.generators])
    
    def _convert_DictComp(self, n):
        c = self._convert
        return DictComp(c(n.key), c(n.value), [c(x) for x in n.generators])
    
    def _convert_comprehension(self, n):
        c = self._convert
        return Comprehension(c(n.target), c(n.iter), [c(x) for x in n.ifs])
    
    ## Statements
    
    def _convert_Assign(self, n):
        c = self._convert
        return Assign([c(x) for x in n.targets], c(n.value))
    
    def _convert_AugAssign(self, n):
        op = n.op.__class__.__name__
        return AugAssign(self._convert(n.target), op, self._convert(n.value))
    
    def _convert_Print(self, n):  # pragma: no cover - Python 2.x compat
        c = self._convert
        if len(n.values) == 1 and isinstance(n.values[0], ast.Tuple):
            arg_nodes = [c(x) for x in n.values[0].elts]
        else:
            arg_nodes = [c(x) for x in n.values]
        kwarg_nodes = []
        if n.dest is not None:
            kwarg_nodes.append(Keyword('dest', c(n.dest)))
        if not n.nl:
            kwarg_nodes.append(Keyword('end', Str('')))
        return Expr(Call(Name('print'), arg_nodes, kwarg_nodes))
    
    def _convert_Exec(self, n):  # pragma: no cover - Python 2.x compat
        c = self._convert
        arg_nodes = [c(n.body)]
        arg_nodes.append(c(n.globals) or NameConstant(None))
        arg_nodes.append(c(n.locals) or NameConstant(None))
        return Expr(Call(Name('exec'), arg_nodes, []))
    
    def _convert_Repr(self, n):  # pragma: no cover - Python 2.x compat
        c = self._convert
        return Call(Name('repr'), [c(n.value)], [])
    
    def _convert_Raise(self, n):
        if pyversion < (3, ):
            if n.inst or n.tback:
                raise RuntimeError('Commonast does not support old raise syntax')
            return Raise(self._convert(n.type), None)
        return Raise(self._convert(n.exc), self._convert(n.cause))
    
    def _convert_Assert(self, n):
        return Assert(self._convert(n.test), self._convert(n.msg))
    
    def _convert_Delete(self, n):
        c = self._convert
        return Delete([c(x) for x in n.targets])
    
    def _convert_Pass(self, n):
        return Pass()
    
    def _convert_Import(self, n):
        return Import(None, [(x.name, x.asname) for x in n.names], 0)
    
    def _convert_ImportFrom(self, n):
        names = [(x.name, x.asname) for x in n.names]
        return Import(n.module, names, n.level)
    
    ## Control flow
    
    def _convert_If(self, n):
        c = self._convert
        node = If(c(n.test), [], [])
        self._stack.append((node.body_nodes, n.body))
        self._stack.append((node.else_nodes, n.orelse))
        return node
    
    def _convert_For(self, n):
        c = self._convert
        node = For(c(n.target), c(n.iter), [], [])
        self._stack.append((node.body_nodes, n.body))
        self._stack.append((node.else_nodes, n.orelse))
        return node
    
    def _convert_While(self, n):
        c = self._convert
        node = While(c(n.test), [], [])
        self._stack.append((node.body_nodes, n.body))
        self._stack.append((node.else_nodes, n.orelse))
        return node
    
    def _convert_Break(self, n):
        return Break()
    
    def _convert_Continue(self, n):
        return Continue()
    
    def _convert_Try(self, n):
        c = self._convert
        node = Try([], [c(x) for x in n.handlers], [], [])
        self._stack.append((node.body_nodes, n.body))
        self._stack.append((node.else_nodes, n.orelse))
        self._stack.append((node.finally_nodes, n.finalbody))
        return node
    
    def _convert_TryFinally(self, n):  # pragma: no cover - Py <= 3.2
        c = self._convert
        if (len(n.body) == 1) and n.body[0].__class__.__name__ == 'TryExcept':
            # un-nesting for try-except-finally
            n2 = n.body[0]
            node = Try([], [c(x) for x in n2.handlers], [], [])
            self._stack.append((node.body_nodes, n2.body))
            self._stack.append((node.else_nodes, n2.orelse))
            self._stack.append((node.finally_nodes, n.finalbody))
        else:
            node = Try([], [], [], [])
            self._stack.append((node.body_nodes, n.body))
            self._stack.append((node.finally_nodes, n.finalbody))
        return node
    
    def _convert_TryExcept(self, n):  # pragma: no cover - Py <= 3.2
        c = self._convert
        node = Try([], [c(x) for x in n.handlers], [], [])
        self._stack.append((node.body_nodes, n.body))
        self._stack.append((node.else_nodes, n.orelse))
        return node
    
    def _convert_ExceptHandler(self, n):
        c = self._convert
        name = n.name.id if isinstance(n.name, ast.Name) else n.name
        node = ExceptHandler(c(n.type), name, [])
        self._stack.append((node.body_nodes, n.body))
        return node
    
    def _convert_With(self, n):
        c = self._convert
        if hasattr(n, 'items'):
            node = With([c(x) for x in n.items], [])
        else:  # pragma: no cover - Py < 3.3
            items = [WithItem(c(n.context_expr), c(n.optional_vars))]
            while (len(n.body) == 1) and isinstance(n.body[0], n.__class__):
                n = n.body[0]
                items.append(WithItem(c(n.context_expr), c(n.optional_vars)))
            node = With(items, [])
        self._stack.append((node.body_nodes, n.body))
        return node
    
    def _convert_withitem(self, n):
        return WithItem(self._convert(n.context_expr), self._convert(n.optional_vars))
    
    ## Function and class definitions
    
    def _convert_FunctionDef(self, n):
        c = self._convert
        args = n.args
        # Parse arg_nodes and kwarg_nodes
        arg_nodes = [c(x) for x in args.args]
        for i, default in enumerate(reversed(args.defaults)):
            arg_node = arg_nodes[-1-i]
            if isinstance(arg_node, Tuple):
                raise RuntimeError('Tuple arguments in function def not supported.')
            arg_node.value_node = c(default)
        if pyversion < (3, ):
            kwarg_nodes = []
        else:
            kwarg_nodes = [c(x) for x in args.kwonlyargs]
            for i, default in enumerate(reversed(args.kw_defaults)):
                kwarg_nodes[-1-i].value_node = c(default) 
        # Parse args_node and kwargs_node
        if pyversion < (3, ):
            args_node = Arg(args.vararg, None, None) if args.vararg else None
            kwargs_node = Arg(args.kwarg, None, None) if args.kwarg else None
        elif pyversion < (3, 4):
            args_node = kwargs_node = None
            if args.vararg:
                args_node = Arg(args.vararg, None, c(args.varargannotation))
            if args.kwarg: 
                kwargs_node = Arg(args.kwarg, None, c(args.kwargannotation))
        else:
            args_node = c(args.vararg)
            kwargs_node = c(args.kwarg)
        
        returns = None if pyversion < (3, ) else c(n.returns)
        node = FunctionDef(n.name, [c(x) for x in n.decorator_list], returns,
                           arg_nodes, kwarg_nodes, args_node, kwargs_node,
                           [])
        if docheck:
            assert isinstance(node.args_node, (NoneType, Arg))
            assert isinstance(node.kwargs_node, (NoneType, Arg))
            for x in node.arg_nodes + node.kwarg_nodes:
                assert isinstance(x, Arg)
        
        self._stack.append((node.body_nodes, n.body))
        return node
    
    def _convert_Lambda(self, n):
        c = self._convert
        args = n.args
        arg_nodes = [c(x) for x in args.args]
        for i, default in enumerate(reversed(args.defaults)):
            arg_nodes[-1-i].value_node = c(default)
        if pyversion < (3, ):
            kwarg_nodes = []
        else:
            kwarg_nodes = [c(x) for x in args.kwonlyargs]
            for i, default in enumerate(reversed(args.kw_defaults)):
                kwarg_nodes[-1-i].value_node = c(default)
        
        return Lambda(arg_nodes, kwarg_nodes,
                      c(args.vararg), c(args.kwarg), c(n.body))
        
    def _convert_arg(self, n):
        # Value is initially None
        return Arg(n.arg or None, None, self._convert(n.annotation))
    
    def _convert_Return(self, n):
        return Return(self._convert(n.value))
    
    def _convert_Yield(self, n):
        return Yield(self._convert(n.value))
    
    def _convert_YieldFrom(self, n):
        return YieldFrom(self._convert(n.value))
    
    def _convert_Global(self, n):
        return Global(n.names)
    
    def _convert_Nonlocal(self, n):
        return Nonlocal(n.names)
    
    def _convert_ClassDef(self, n):
        c = self._convert
        arg_nodes = [c(a) for a in n.bases]
        kwarg_nodes = [] if pyversion < (3, ) else [c(a) for a in n.keywords]
        
        if getattr(n, 'starargs', None):
            arg_nodes.append(Starred(self._convert(n.starargs)))
        if getattr(n, 'kwargs', None):
            kwarg_nodes.append(Keyword(None, self._convert(n.kwargs)))
        
        node = ClassDef(n.name, [c(a) for a in n.decorator_list],
                        arg_nodes, kwarg_nodes, [])
        
        self._stack.append((node.body_nodes, n.body))
        return node
