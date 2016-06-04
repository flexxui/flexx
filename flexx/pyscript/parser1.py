"""

The basics
----------

Most types just work, common Python names are converted to their JavaScript
equivalents.

.. pyscript_example::
    
    # Simple operations
    3 + 4 -1
    3 * 7 / 9
    5**2
    pow(5, 2)
    7 // 2
    
    # Basic types
    [True, False, None]
    
    # Lists and dicts
    foo = [1, 2, 3]
    bar = {'a': 1, b: 2}


Slicing and subscriping
-----------------------

.. pyscript_example::

    # Slicing lists
    foo = [1, 2, 3, 4, 5]
    foo[2:]
    foo[2:-2]
    
    # Slicing strings
    bar = 'abcdefghij'
    bar[2:]
    bar[2:-2]
    
    # Subscripting
    foo = {'bar': 3}
    foo['bar']
    foo.bar  # Works in JS, but not in Python


String formatting
-----------------

Basic string formatting is supported for "%s", "%f", and "%i".

.. pyscript_example::
    
    "value: %f" % val
    "%s: %f" % (name, val)


Assignments
-----------

Declaration of variables is handled automatically. Also support for
tuple packing and unpacking (a.k.a. destructuring assignment).

.. pyscript_example::
    
    # Declare foo
    foo = 3
    
    # But not here
    bar.foo = 3
    
    # Pack items in an array
    a = 1, 2, 3
    
    # And unpack them
    a1, a2, a3 = a
    
    # Deleting variables
    del bar.foo
    
    # Functions starting with a capital letter
    # are assumed constructors
    foo = Foo()


Comparisons
-----------

.. pyscript_example::
    
    # Identity
    foo is bar
    
    # Equality 
    foo == bar
    
    # But comparisons are deep (unlike JS)
    (2, 3, 4) == (2, 3, 4)
    (2, 3) in [(1,2), (2,3), (3,4)]

    # Test for null
    foo is None
    
    # Test for JS undefined
    foo is undefined
    
    # Testing for containment
    "foo" in "this has foo in it"
    3 in [0, 1, 2, 3, 4]


Truthy and Falsy
----------------

In JavaScript, an empty array and an empty dict are interpreted as
truthy. PyScript fixes this, so that you can do ``if an_array:`` as
usual.

.. pyscript_example::

    # These evaluate to False:
    0
    NaN
    ""  # empty string
    None  # JS null
    undefined
    []
    {}
    
    # This still works
    a = []
    a = a or [1]  # a is now [1]


Function calls
--------------

As in Python, the default return value of a function is ``None`` (i.e.
``null`` in JS).

.. pyscript_example::
    
    # Business as usual
    foo(a, b)
    
    # Support for star args (but not **kwargs)
    foo(*a)

Imports
-------

PyScript has limited support for imports. At this point, only a few
objects from ``time`` and ``sys`` are supported. Module support may be
extended in the future.

.. pyscript_example::
    
    # Get time (number of seconds since epoch)
    import time
    print(time.time())
    
    # High resolution timer (as in time.perf_counter on Python 3)
    import time
    t0 = time.perf_counter()
    do_something()
    t1 = time.perf_counter()
    print('this took me', t1-t0, 'seconds')

"""

import re

from . import commonast as ast
from . import stdlib
from .parser0 import Parser0, JSError, unify, reprs  # noqa


# Define buildin stuff for which we know that it returns a bool or int
_bool_funcs = 'hasattr', 'contains', 'all', 'any', 'equals', 'truthy'
_bool_meths = ('count', 'isalnum', 'isalpha', 'isidentifier', 'islower',
               'isnumeric', 'isspace', 'istitle', 'isupper', 'startswith')
returning_bool = tuple([stdlib.FUNCTION_PREFIX + x + '(' for x in _bool_funcs] +
                       [stdlib.METHOD_PREFIX + x + '.' for x in _bool_meths])


class Parser1(Parser0):
    """ Parser that add basic functionality like assignments,
    operations, function calls, and indexing.
    """
    
    ## Literals
    
    def parse_Num(self, node):
        return repr(node.value)
    
    def parse_Str(self, node):
        return reprs(node.value)
    
    def parse_Bytes(self, node):
        raise JSError('No Bytes in JS')
    
    def parse_NameConstant(self, node):
        M = {True: 'true', False: 'false', None: 'null'}
        return M[node.value]
    
    def parse_List(self, node):
        code = ['[']
        for child in node.element_nodes:
            code += self.parse(child)
            code.append(', ')
        if node.element_nodes:
            code.pop(-1)  # skip last comma
        code.append(']')
        return code
    
    def parse_Tuple(self, node):
        return self.parse_List(node)  # tuple = ~ list in JS
    
    def parse_Dict(self, node):
        code = ['{']
        for key, val in zip(node.key_nodes, node.value_nodes):
            code += self.parse(key)
            code.append(': ')
            code += self.parse(val)
            code.append(', ')
        if node.key_nodes:
            code.pop(-1)  # skip last comma
        code.append('}')
        return code
        
    def parse_Set(self, node):
        raise JSError('No Set in JS')
    
    ## Variables
    
    def parse_Name(self, node):
        # node.ctx can be Load, Store, Del -> can be of use somewhere?
        name = node.name
        if name in self.vars:
            name = self.with_prefix(name)
        else:
            name = self.NAME_MAP.get(name, name)
        return name
    
    def parse_Starred(self, node):
        # they're present in Call arguments, but we parse them there.
        raise JSError('Starred args are not supported.')
    
    ## Expressions
    
    def parse_Expr(self, node):
        # Expression (not stored in a variable)
        code = [self.lf()]
        code += self.parse(node.value_node)
        code.append(';')
        return code
    
    def parse_UnaryOp(self, node):
        if node.op == node.OPS.Not:
            return '!', self._wrap_truthy(node.right_node)
        else:
            op = self.UNARY_OP[node.op]
            right = unify(self.parse(node.right_node))
            return op, right
    
    def parse_BinOp(self, node):
        if node.op == node.OPS.Mod and isinstance(node.left_node, ast.Str):
            # Modulo on a string is string formatting in Python
            return self._format_string(node)
        
        left = unify(self.parse(node.left_node))
        right = unify(self.parse(node.right_node))
        
        if node.op == node.OPS.Add:
            C = ast.Num, ast.Str
            if not (isinstance(node.left_node, C) or isinstance(node.right_node, C)):
                return self.use_std_function('add', [left, right])
        elif node.op == node.OPS.Mult:
            C = ast.Num
            if not (isinstance(node.left_node, C) and isinstance(node.right_node, C)):
                return self.use_std_function('mult', [left, right])
        elif node.op == node.OPS.Pow:
            return ["Math.pow(", left, ", ", right, ")"]
        elif node.op == node.OPS.FloorDiv:
            return ["Math.floor(", left, "/", right, ")"]
        
        op = ' %s ' % self.BINARY_OP[node.op]
        return [left, op, right]
    
    def _format_string(self, node):
        # Get left end, stripped from the separator
        left = ''.join(self.parse(node.left_node))
        sep, left = left[0], left[1:-1]
        # Get items
        right = node.right_node
        if isinstance(right, (ast.Tuple, ast.List)):
            items = [unify(self.parse(n)) for n in right.element_nodes]
        else:
            items = [unify(self.parse(right))]
        # Get matches
        matches = list(re.finditer(r'%[0-9\.\+\-\#]*[srdeEfgGioxXc]', left))
        if len(matches) != len(items):
            raise JSError('In string formatting, number of placeholders '
                            'does not match number of replacements')
        # Format
        code = []
        start = 0
        for i, m in enumerate(matches):
            fmt = m.group(0)
            if fmt in ('%s', '%f', '%i', '%d', '%g'):
                code.append(sep + left[start:m.start()] + sep)
                code.append(' + ' + items[i] + ' + ')
            elif fmt == '%r':
                code.append(sep + left[start:m.start()] + sep)
                code.append(' + JSON.stringify(%s) + ' % items[i])
            else:
                raise JSError('Unsupported string formatting %r' % fmt)
            start = m.end()
        code.append(sep + left[start:] + sep)
        return code
    
    def _wrap_truthy(self, node):
        """ Wraps an operation in a truthy call, unless its not necessary. """
        eq_name = stdlib.FUNCTION_PREFIX + 'equals'
        test = ''.join(self.parse(node))
        if (False or test.endswith('.length') or test.startswith('!') or
                     test.isnumeric() or test == 'true' or test == 'false' or
                     test.count('==') or test.count(eq_name) or
                     test == '"this_is_js()"' or
                     (test.startswith(returning_bool) and '||' not in test)):
            return unify(test)
        else:
            return self.use_std_function('truthy', [test])
    
    def parse_BoolOp(self, node):
        op = ' %s ' % self.BOOL_OP[node.op]
        if node.op.lower() == 'or':  # allow foo = bar or []
            values = [unify(self._wrap_truthy(val)) for val in node.value_nodes[:-1]]
            values += [unify(self.parse(node.value_nodes[-1]))]
        else:
            values = [unify(self._wrap_truthy(val)) for val in node.value_nodes]
        return op.join(values)
    
    def parse_Compare(self, node):
        
        left = unify(self.parse(node.left_node))
        right = unify(self.parse(node.right_node))
        
        if node.op in (node.COMP.Eq, node.COMP.NotEq):
            code = self.use_std_function('equals', [left, right])
            if node.op == node.COMP.NotEq:
                code = '!' + code
            return code
        elif node.op in (node.COMP.In, node.COMP.NotIn):
            self.use_std_function('equals', [])  # trigger use of equals
            code = self.use_std_function('contains', [left, right])
            if node.op == node.COMP.NotIn:
                code = '!' + code
            return code
        else:
            op = self.COMP_OP[node.op]
            return "%s %s %s" % (left, op, right)
    
    def parse_Call(self, node):
        
        # Get full function name and method name if it exists
        
        if isinstance(node.func_node, ast.Attribute):
            method_name = node.func_node.attr
            base_name = unify(self.parse(node.func_node.value_node))
            full_name = base_name + '.' + method_name
        elif isinstance(node.func_node, ast.Subscript):
            base_name = unify(self.parse(node.func_node.value_node))
            full_name = unify(self.parse(node.func_node))
            method_name = ''
        else:  # ast.Name
            method_name = ''
            base_name = ''
            full_name = unify(self.parse(node.func_node))
        
        # Handle imports
        imported = self._imports.get(base_name)
        if imported:
            full_name = self.use_imported_object(imported + '.' + method_name)
        
        # Handle special functions and methods
        res = None
        if method_name in self._methods:
            res = self._methods[method_name](node, base_name)
        elif full_name in self._functions:
            res = self._functions[full_name](node)
        if res is not None:
            return res
        
        # Handle normally
        if base_name.endswith('._base_class') or base_name == 'super()':
            # super() was used, use "call" to pass "this"
            return [full_name] + self._get_args(node, 'this', True)
        else:
            code = [full_name] + self._get_args(node, base_name)
            # Insert "new" if this looks like a class
            if base_name == 'this':
                pass
            elif method_name:
                if method_name[0].lower() != method_name[0]:
                    code.insert(0, 'new ')
            else:
                fn = full_name
                if fn in self._seen_func_names and fn not in self._seen_class_names:
                    pass
                elif fn not in self._seen_func_names and fn in self._seen_class_names:
                    code.insert(0, 'new ')
                elif full_name[0].lower() != full_name[0]:
                    code.insert(0, 'new ')
            return code
    
    def _get_args(self, node, base_name, use_call_or_apply=False):
        """ Get arguments for function call. Does checking for keywords and
        handles starargs. The first element in the returned list is either
        "(" or ".apply(".
        """
        # Check for keywords (not supported) after handling special functions
        if node.kwarg_nodes:
            raise JSError('function calls do not support keyword arguments or kwargs')
        
        base_name = base_name or 'null'
        
        # flatten args and add commas
        use_starargs = False
        argswithcommas = []
        arglists = [argswithcommas]
        for arg in node.arg_nodes:
            if isinstance(arg, ast.Starred):
                use_starargs = True
                starname = ''.join(self.parse(arg.value_node))
                arglists.append(starname)
                argswithcommas = []
                arglists.append(argswithcommas)
            else:
                argswithcommas.extend(self.parse(arg))
                argswithcommas.append(', ')
        
        # Clear empty lists and trailing commas
        for i in reversed(range(len(arglists))):
            arglist = arglists[i]
            if not arglist:
                arglists.pop(i)
            elif arglist[-1] == ', ':
                arglist.pop(-1)
        
        if use_starargs:
            # Note that this goes wrong if the original code uses apply()
            code = ['.apply(', base_name, ', ']
            if len(arglists) == 1:
                # the concat thing does not seem to work well with "arguments"
                code += starname, ')'
            else:
                code += ['[].concat(']
                for arglist in arglists:
                    if isinstance(arglist, list):
                        code += ['[']
                        code += arglist
                        code += [']']
                    else:
                        code += [arglist]
                    code += [', ']
                code.pop(-1)
                code += '))'
            return code
        elif use_call_or_apply:
            if argswithcommas:
                return [".call(", base_name, ', '] + argswithcommas + [")"]
            else:
                return [".call(", base_name, ")"]
        else:
            # Normal func
            return ["("] + argswithcommas + [")"]
    
    def parse_Attribute(self, node):
        base_name = unify(self.parse(node.value_node))
        # Handle imports
        imported = self._imports.get(base_name)
        if imported:
            return self.use_imported_object(imported + '.' + node.attr)
        # Handle normally
        return "%s.%s" % (base_name, self.ATTRIBUTE_MAP.get(node.attr, node.attr))
    
    ## Statements
    
    def parse_Assign(self, node):
        """ Variable assignment. """
        code = [self.lf()]
        
        # Parse targets
        tuple = []
        for target in node.target_nodes:
            var = ''.join(self.parse(target))
            if isinstance(target, ast.Name):
                if '.' in var:
                    code.append(var)
                else:
                    self.vars.add(var)
                    code.append(self.with_prefix(var))
            elif isinstance(target, ast.Attribute):
                code.append(var)
            elif isinstance(target, ast.Subscript):
                code.append(var)
            elif isinstance(target, (ast.Tuple, ast.List)):
                dummy = self.dummy()
                code.append(dummy)
                tuple = target.element_nodes
            else:
                raise JSError("Unsupported assignment type")
            code.append(' = ')
        
        # Parse right side
        code += self.parse(node.value_node)
        code.append(';')
        
        # Handle tuple unpacking
        if tuple:
            code.append(self.lf())
            for i, x in enumerate(tuple):
                var = unify(self.parse(x))
                if isinstance(x, ast.Name):  # but not when attr or index
                    self.vars.add(var)
                code.append('%s = %s[%i];' % (var, dummy, i))
        
        return code
    
    def parse_AugAssign(self, node):  # -> x += 1
        target = ''.join(self.parse(node.target_node))
        value = ''.join(self.parse(node.value_node))
        
        nl = self.lf()
        if node.op == node.OPS.Add:
            return [nl, target, '=', self.use_std_function('add', [target, value])]
        elif node.op == node.OPS.Mult:
            return [nl, target, '=', self.use_std_function('mult', [target, value])]
        elif node.op == node.OPS.Pow:
            return [nl, target, " = Math.pow(", target, ", ", value, ")"]
        elif node.op == node.OPS.FloorDiv:
            return [nl, target, " = Math.floor(", target, "/", value, ")"]
        else:
            op = ' %s= ' % self.BINARY_OP[node.op]
            return [nl, target, op, value, ';']
    
    def parse_Delete(self, node):
        code = []
        for target in node.target_nodes:
            code.append(self.lf('delete '))
            code += self.parse(target)
            code.append(';')
        return code
    
    def parse_Pass(self, node):
        return []

    ## Subscripting
    
    def parse_Subscript(self, node):
        
        value_list = self.parse(node.value_node)
        slice_list = self.parse(node.slice_node)
        
        code = []
        code += value_list
        
        if isinstance(node.slice_node, ast.Index):
            code.append('[')
            if slice_list[0].startswith('-'):
                code.append(unify(value_list) + '.length ')
            code += slice_list
            code.append(']')
        else:  # ast.Slice
            code.append('.slice(')
            code += slice_list
            code.append(')')
        return code
    
    def parse_Index(self, node):
        return self.parse(node.value_node)
    
    def parse_Slice(self, node):
        code = []
        if node.step_node:
            raise JSError('Slicing with step not supported.')
        if node.lower_node:
            code += self.parse(node.lower_node)
        else:
            code.append('0')
        if node.upper_node:
            code.append(',')
            code += self.parse(node.upper_node)
        return code
    
    def parse_ExtSlice(self, node):
        raise JSError('Multidimensional slicing not supported in JS')
    
    ## Imports 

    def parse_Import(self, node):
        
        if node.root and node.root.endswith('pyscript'):
            # User is probably importing names from here to allow
            # writing the JS code and command to parse it in one module.
            # Ignore this import.
            return []
        if node.root and node.root == '__future__':
            return []  # stuff to help the parser
        
        if node.level:
            raise JSError('PyScript does not support relative imports.')
        
        root = node.root + '.' if node.root else ''
        names = [name[0] for name in node.names]
        aliases = [name[1] for name in node.names]
        
        code = []
        for name, alias in zip(names, aliases):
            full_name = root + name
            alias = alias if alias else name
            if full_name in stdlib.IMPORTS:
                if stdlib.IMPORTS[full_name] is None:
                    # Register the module for later attribute lookup 
                    self._imports[alias] = full_name
                else:
                    # Import the object
                    realname = self.use_imported_object(full_name)
                    code += [self.lf(), 'var %s = %s;' % (alias, realname)]
            else:
                raise JSError('Unknown import %r' % name)
        return code
    
    def parse_Module(self, node):
        # Module level. Every piece of code has a module as the root.
        # Just pass body.
        
        # Get docstring, but only if in module mode (i.e. top stack has a name)
        docstring = ''
        if self._docstrings and self._stack[0][1]:
            docstring = self.pop_docstring(node)
        
        code = []
        if docstring:
            for line in docstring.splitlines():
                code.append(self.lf('// ' + line))
            code.append('\n')
        for child in node.body_nodes:
            code += self.parse(child)
        return code
