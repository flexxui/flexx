"""
Module that defines a common AST description, and has a parser to
generate this common AST by using the buildin ast module and converting
the result.
"""

import sys
import ast
import json
import base64

pyversion = sys.version_info


def parse(code):
    """ Parse the given string of Python code and return an AST tree.
    """
    root = ast.parse(code)
    converter = NativeAstConverter()
    return converter.convert(root)


class Node:
    """ Abstract base class for all Nodes.
    """
    
    __slots__ = []
    
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
        In = 'NotIn'
    
    def __init__(self, *args):
        assert not hasattr(self, '__dict__'), 'Nodes must have __slots__'
        assert not self.__class__ is Node, 'Node is an abstract class'
        names = self._get_names()
        assert len(args) == len(names)
        for name, val in zip(names, args):
            # Check if the value is what we expect it to be given its name
            assert not isinstance(val, ast.AST)
            if name == 'name':
                assert isinstance(val, str), 'name is not a string'
            elif name == 'op':
                assert val in Node.OPS.__dict__ or val in Node.COMP.__dict__
            elif name.endswith('_node'):
                assert isinstance(val, (Node, None.__class__)), '%r is not a Node instance' % name
            elif name.endswith('_nodes'):
                islistofnodes = isinstance(val, list) and all(isinstance(n, Node) for n in val)
                assert islistofnodes, '%r is not a list of nodes' % name
            else:
                assert not isinstance(val, Node), '%r should not be a Node instance' % name
            # Assign
            setattr(self, name, val)
    
    def _get_names(self):
        return tuple(self.__slots__)
        #return self.__init__.__func__.__code__.co_varnames[1:]
    
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
        for name in Cls.__init__.__code__.co_varnames[1:]:
            val = d[name]
            if val == 'null':
                val = None
            elif name.endswith('_node'):
                val = Node._fromdict(val)
            elif name.endswith('_nodes'):
                val = [Node._fromdict(x) for x in val]
            elif isinstance(val, str) and val.startswith('BYTES:'):
                val = base64.decodebytes(val[6:])
            args.append(val)
        return Cls(*args)
    
    def _todict(self):
        """ Get a dict representing this AST. This is the basis for
        creating JSON, but can be used to compare AST trees as well.
        """
        d = {}
        d['_type'] = self.__class__.__name__
        for name in self._get_names():
            val = getattr(self, name)
            if val is None:
                val = 'null'
            elif name.endswith('_node'):
                val = val._todict()
            elif name.endswith('_nodes'):
                val = [x._todict() for x in val]
            elif isinstance(val, bytes):
                val = 'BYTES:' + base64.encodebytes(val).decode().rstrip()
            d[name] = val
        return d
    
    def __eq__(self, other):
        assert isinstance(other, Node)
        return self._todict() == other._todict()
    
    def __repr__(self):
        names = ', '.join([repr(x) for x in self._get_names()])
        return '<%s with %s at 0x%x>' % (self.__class__.__name__, names, id(self))
    
    def __str__(self):
        return self.tojson()
    
    def _append_to_parent_body(self, parent):
        parent.body_nodes.append(self)
    

Node.OPS.__doc__ += ', '.join([x for x in sorted(Node.OPS.__dict__) if not x.startswith('_')])
Node.COMP.__doc__ += ', '.join([x for x in sorted(Node.COMP.__dict__) if not x.startswith('_')])

## -- (start marker for doc generator)

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
    """ A starred variable name, e.g. ``*foo``. Note that this isn’t
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
        value_nodes: a list with one node (i.e. the operand).
    """
    __slots__ = 'op', 'value_nodes'

class BinOp(Node):
    """ A binary operation (e.g. ``a / b``, ``a + b``).
    
    Attributes:
        op: the operator (an enum from ``Node.OPS``).
        value_nodes: a list with two nodes (the one to the left and the
            one to the right of the operator).
    """
    __slots__ = 'op', 'value_nodes'

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
        value_nodes: a list with two nodes (the one to the left and the
            one to the right of the operator).
    """
    __slots__ = 'op', 'value_nodes'

class Call(Node):
    """ A function call.
    
    Attributes:
        func_node: Name or Attribute node that represents the function.
        arg_nodes: list of nodes representing positional arguments.
        kwarg_nodes: list of Keyword nodes representing keyword arguments.
    
    Note that an argument ``*x`` would be specified as a Starred node
    in arg_nodes, and ``**y`` as a Keyword node with a name being ``None``.
    """
    __slots__ = ('func_node', 'arg_nodes', 'kwarg_nodes')

class Keyword(Node):
    """ Keyword argument used in a Call.
    
    Attributes:
        name: the (string) name of the argument.
        value_node: the value of the arg. 
    """
    _slots__ = ('name', 'value_node')

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

class DictExp(Node):
    """ Dict comprehension.
    
    Attributes:
        key_node: the key of the item being evaluated.
        value_node: the value of the item being evaluated.
        comp_nodes: a list of Comprehension nodes.
    """
    __slots__ = 'key_node', 'value_node',  'comp_nodes'

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
    
    Note that elif clauses don’t have a special representation in the
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
        kwarg_nodes: list of Arg nodes representing keyword arguments.
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
        kwarg_nodes: list of Arg nodes representing keyword arguments.
        args_node: an Arg node representing ``*args``.
        kwargs_node: an Arg node representing ``**kwargs``.
        body_nodes: the body of the function.
    """
    __slots__ = ('arg_nodes', 'kwarg_nodes', 'args_node', 'kwargs_node', 
                 'body_nodes')
    
class Arg(Node):
    """ Function argument for a FunctionDef.
    
    Attributes:
        name: the (string) name of the argument.
        value_node: the default value of this argument. Can be None.
        annotation_node: the annotation for this argument (Python3 only).
    """
    
    __slots__ = ('name', 'value_node', 'annotation_node')

class Return(Node):
    """ A return statement.
    """
    __slots__ = ()

class Yield(Node):
    """ Yield expression.
    """
    __slots__ = ()

class YieldFrom(Node):
    """ YieldFrom expression.
    """
    __slots__ = ()

class Global(Node):
    """
    Attributes:
        names: a list of variable names to declare global.
    """
    __slots__ = 'names',

class Nonlocal(Node):
    """
    Attributes:
        names: a list of variable names to declare nonlocal.
    """
    __slots__ = 'names',

class ClassDef(Node):
    """ A class definition.
    
    Attributes:
        name: a string for the class name.
        decorator_nodes: the list of decorators to be applied, as in FunctionDef.
        arg_nodes: list of nodes representing base classes.
        kwarg_nodes: list of Keyword nodes representing keyword arguments.
        body_nodes: the body of the class.
    
    Note that an argument ``*x`` would be specified as a Starred node
    in arg_nodes, and ``**y`` as a Keyword node with a name being ``None``.
    """
    __slots__ = ('name', 'decorator_nodes', 'arg_nodes', 'kwarg_nodes', 'body_nodes')

## -- (end marker for doc generator)


class NativeAstConverter:
    """ Convert ast produced bt Python's ast module to common ast.
    """
    
    def __init__(self):
        self._stack = []
    
    def convert(self, root):
        assert not self._stack
        
        result = self._convert(root)
        
        while self._stack:
            native_node, parent = self._stack.pop(0)
            node = self._convert(native_node)
            if parent is not None:
                node._append_to_parent_body(parent)
        
        return result
    
    def _convert(self, n):
        # n is the native node produced by the ast module
        
        # Some node attributes can be None
        if n is None:
            return None
        
        type = n.__class__.__name__
        converter = getattr(self, '_convert_' + type, None)
        if converter:
            val = converter(n)
            assert isinstance(val, Node)
            return val
        else:
            raise RuntimeError('%s cannot convert %s nodes.' % (self.__class__.__name__, type))
    
    def _listconvert(self, *nn):
        if len(nn) == 1 and isinstance(nn[0], (tuple, list)):
            nn = nn[0]
        return [self._convert(n) for n in nn]
    
    def _convert_Module(self, n):
        node = Module([])
        for sub in n.body:
            self._stack.append((sub, node))
        return node
    
    ## Literals
    
    def _convert_Num(self, n):
        return Num(n.n)
        
    def _convert_Str(self, n):
        return Str(n.s)
    
    def _convert_Bytes(self, n):
        return Bytes(n.s)
    
    def _convert_List(self, n):
        return List(self._listconvert(n.elts))
    
    def _convert_Tuple(self, n):
        return Tuple(self._listconvert(n.elts))
    
    def _convert_Set(self, n):
        return Set(self._listconvert(n.elts))
    
    def _convert_Dict(self, n):
        return Dict(self._listconvert(n.keys), self._listconvert(n.values))
    
    def _convert_Ellipses(self, n):
        return Ellipsis()
    
    def _convert_NameConstant(self, n):
        return NameConstant(n.value)
    
    ## Variables, attributes, indexing and slicing
    
    def _convert_Name(self, n):
        M = {'None': None, 'False': False, 'True': True}
        if pyversion < (3, 4) and n.id in M:
            return NameConstant(M[n.id])  # Python < 3.4
        return Name(n.id)
    
    def _convert_Starred(self, n):
        return Starred(self._convert(n.value))
    
    def _convert_Attribute(self, n):
        return Attribute(self._convert(n.value), n.attr)
    
    def _convert_SubScript(self, n):
        return Subscript(self._convert(n.value), self._convert(n.slice))
    
    def _convert_Index(self, n):
        return Index(self._convert(n.slice.value))
    
    def _convert_Slice(self, n):
        return Slice(*self._listconvert(n.lower, n.upper, n.step))
    
    def _convert_ExtSlice(self, n):
        return ExtSlice(self._listconvert(n.dims))
    
    ## Expressions
    
    def _convert_Expr(self, n):
        return Expr(self._convert(n.value))
    
    def _convert_UnaryOp(self, n):
        op = n.op.__class__.__name__
        return UnaryOp(op, self._listconvert([n.operand]))
    
    def _convert_BinOp(self, n):
        op = n.op.__class__.__name__
        return BinOp(op, self._listconvert([n.left, n.right]))
    
    def _convert_BoolOp(self, n):
        op = n.op.__class__.__name__
        return BoolOp(op, self._listconvert(n.values))
    
    def _convert_Compare(self, n):
        # Get compares and ops
        comps = self._listconvert([n.left] + n.comparators)
        ops = [op.__class__.__name__ for op in n.ops]
        assert len(ops) == (len(comps) - 1)
        # Create our comparison operators
        compares = []
        for i in range(len(ops)):
            co = Compare(ops[i], [comps[i], comps[i+1]])
            compares.append(co)
        # Return single or wrapped in an AND
        assert compares
        if len(compares) == 1:
            return compares[0]
        else:
            return BoolOp(Node.OPS.And, compares)
    
    def _convert_Call(self, n):
        arg_nodes = [self._convert(a) for a in n.args]
        kwarg_nodes = [self._convert(a) for a in n.keywords]
        
        if pyversion < (3, 5):
            if n.starargs:
                arg_nodes.append(Starred(self._convert(n.starargs)))
            if n.kwargs:
                kwarg_nodes.append(Keyword(None, self._convert(n.kwargs)))
        
        return Call(self._convert(n.func), arg_nodes, kwarg_nodes)
    
    def _convert_keyword(self, n):
        return Keyword(n.arg, self._convert(n.value))
    
    def _convert_IfExp(self, n):
        c = self._convert
        return IfExp(c(n.test), c(n.body), c(n.orelse))
    
    def _convert_ListComp(self, n):
        return ListComp(self._convert(n.elt), self._listconvert(n.generators))
    
    def _convert_SetComp(self, n):
        return SetComp(self._convert(n.elt), self._listconvert(n.generators))
    
    def _convert_GeneratorExp(self, n):
        return GeneratorExp(self._convert(n.elt), self._listconvert(n.generators))
    
    def _convert_DictComp(self, n):
        comp_nodes = self._listconvert(n.generators)
        return DictComp(self._convert(n.key), self._convert(n.value), comp_nodes)
    
    def _convert_comprehension(self, n):
        if_nodes = self._listconvert(n.ifs)
        return Comprehension(self._convert(n.target), self._convert(n.iter), if_nodes)
    
    ## Statements
    
    def _convert_Assign(self, n):
        return Assign(self._listconvert(n.targets), self._convert(n.value))
    
    def _convert_AugAssign(self, n):
        op = n.op.__class__.__name__
        return AugAssign(self._convert(n.target), op, self._convert(n.value))
    
    def _convert_Print(self, n):  # pragma: no cover
        # Python 2.x compat
        arg_nodes = self._listconvert(n.values)
        kwarg_nodes = []
        if n.dest is not None:
            kwarg_nodes.append(Keyword('dest', self._convert(n.dest)))
        if not n.nl:
            kwarg_nodes.append(Keyword('end', Str('')))
        return Call(arg_nodes, kwarg_nodes)
    
    def _convert_Raise(self, n):
        return Raise(self._convert(n.exc), self._convert(n.cause))
    
    def _convert_Assert(self, n):
        return Assert(self._convert(n.test), self._convert(n.msg))
    
    def _convert_Delete(self, n):
        return Delete(self._listconvert(n.targets))
    
    def _convert_Pass(self, n):
        return Pass()
    
    def _convert_Import(self, n):
        return Import(None, [(x.name, x.asname) for x in n.names], 0)
    
    def _convert_ImportFrom(self, n):
        names = [(x.name, x.asname) for x in n.names]
        return Import(n.module, names, n.level)
    
    ## Control flow
    
    def _convert_If(self, n):
        c, lc = self._convert, self._listconvert
        return If(c(n.test), lc(n.body), lc(n.orelse))
    
    def _convert_For(self, n):
        c, lc = self._convert, self._listconvert
        return For(c(n.target), c(n.iter), lc(n.body), lc(n.orelse))
    
    def _convert_While(self, n):
        c, lc = self._convert, self._listconvert
        return While(c(n.test), lc(n.body), lc(n.orelse))
    
    def _convert_Break(self, n):
        return Break()
    
    def _convert_Continue(self, n):
        return Continue()
    
    def _convert_Try(self, n):
        c, lc = self._convert, self._listconvert
        return Try(lc(n.body), lc(n.handlers), lc(n.orelse), lc(n.finalbody))
    
    def _convert_TryFinally(self, n):  # Python <= 3.2
        c, lc = self._convert, self._listconvert
        return Try(lc(n.body), [], [], lc(n.finalbody))
    
    def _convert_TryExcept(self, n):  # Python <= 3.2
        c, lc = self._convert, self._listconvert
        return Try(lc(n.body), lc(n.handlers), lc(n.orelse), [])
    
    def _convert_ExceptHandler(self, n):
        c, lc = self._convert, self._listconvert
        return ExceptHandler(lc(n.type), name, lc(n.body))
    
    def _convert_With(self, n):
        return With(self._listconvert(n.items), self._convert(n.body))
    
    def _convert_WithItem(self, n):
        return WithItem(self._convert(n.context_expr), self._convert(n.optional_vars))
    
    ## Function and class definitions
    
    def _convert_FunctionDef(self, n):
        args = n.args
        c = self._convert
        args_nodes = self._listconvert(args.args)
        kwargs_nodes = self._listconvert(args.kwonlyargs)
        for i, default in enumerate(reversed(args.defaults)):
            args_nodes[-1-i].value_node = c(default)
        for i, default in enumerate(reversed(args.kw_defaults)):
            kwargs_nodes[-1-i].value_node = c(default) 
        
        node = FunctionDef(n.name, self._listconvert(n.decorator_list), c(n.returns), 
                           args_nodes, kwargs_nodes, c(args.vararg), c(args.kwarg),
                           [])
        
        for sub in n.body:
            self._stack.append((sub, node))
        return node
    
    def _convert_Lambda(self, n):
        args = n.args
        c = self._convert
        args_nodes = self._listconvert(args.args)
        kwargs_nodes = self._listconvert(args.kwonlyargs)
        for i, default in enumerate(reversed(args.defaults)):
            args_nodes[-1-i].value_node = c(default)
        for i, default in enumerate(reversed(args.kw_defaults)):
            kwargs_nodes[-1-i].value_node = c(default) 
        
        return Lambda(n.name, args_nodes, kwargs_nodes, 
                      c(args.vararg), c(args.kwarg), self._listconvert(n.body))
        
    def _convert_arg(self, n):
        return Arg(n.arg, None, self._convert(n.annotation))  # Value is initially None
    
    def _convert_Return(self, n):
        return Return()
    
    def _convert_Yield(self, n):
        return Yield()
    
    def _convert_YieldFrom(self, n):
        return YieldFrom()
    
    def _convert_Global(self, n):
        return Global()
    
    def _convert_Nonlocal(self, n):
        return Nonlocal()
    
    def _convert_ClassDef(self, n):
        arg_nodes = [self._convert(a) for a in n.args]
        kwarg_nodes = [self._convert(a) for a in n.keywords]
    
        if n.starargs:
            arg_nodes.append(Starred(self._convert(n.starargs)))
        if n.kwargs:
            kwarg_nodes.append(Keyword(None, self._convert(n.kwargs)))
        
        return ClassDef(n.name, self._listconvert(n.decorator_list),
                        arg_nodes, kwarg_nodes, self._listconvert(n.body))


TEST = """
aap = bar = 2 
aap += 2
def foo(a, b, *c):
    return None

foo(a, b, c, d, *e)
""" #.lstrip()
    
if __name__ == '__main__':
    r1 = ast.parse(TEST)
    r2 = parse(TEST)
    # convert_ast(ast.parse(TEST))
