"""

Parts of this code are inspired by / taken from the py2js project.

Useful links:
 * https://greentreesnakes.readthedocs.org/en/latest/nodes.html

Supported basics:

* numbers, strings
* Binary, unary and boolean operations
* power and integer division operations
* multiple variable assignment
* lists, tuples, dicts (respectively become JS arrays, arrays, objects)
* comparisons (== -> ==, is -> ===)
* if-statements and single-line if-expression
* while-loops
* for-loops using range()
* while and for loops support continue, break, and else-clauses
* function calls can have *args (but no keywords or **kwargs)
* function defs can have default arguments, *args (but no kwargs)
* Slicing (though not with step)
* Use of ``self`` is translated to ``this``

Supported Python conveniences:

* print() becomes console.log (no ``end`` and ``sep`` though)
* len(x) becomes x.length 

Not currently supported:

* The ``in`` operator 
* tuple packing/unpacking
* function defs cannot have ``**kwargs``
* cannot call a function with ``*args``
* Exceptions, assertions, delete

Probably never suppored:

* Slicing with steps
* set (JS has no set)
* Most Python buildins
* importing


User guide stuff:
    
    # "self" is replaced with "this"
    self.foo
    
    # Printing just works
    print('some test')
    print(a, b, c, sep='-')
    
    ## For loops
    
    # You can use range for explicit for-loops. You can also iterate
    # directly over values in an array, string or dict. In case of
    # dicts, we using ``.keys()``, ``.values()`` and
    # ``items()`` should provide slightly increased performance.
    
    # Using range() yields true for-loops
    for i in range(10):
        print(i)
    for i in range(100, 10, -2):
        print(i)
    
    # One way to iterate over an array
    for i in range(len(arr)):
        print(arr[i])
    
    # But this is equally valid (and fast)
    for element in arr:
        print(element)
    
    # Similarly, iteration over strings
    for char in "foo bar":
        print(c)
    
    # Plain iteration over a dict costs a small overhead
    for key in d:
        print(key)
        
    # Which is why we recommend the following syntax
    for key in d.keys():
        print(key)
    for val in d.values():
        print(val)
    for key, val in d.items():
        print(key, val, sep=': ')
    
    # Some methods get replaced
    a.append(x)

"""

import re
import inspect
import ast
from astpp import dump, parseprint  # 3d party


class JSError(NotImplementedError):
    pass


class JSFuction:
    """ Definition of a javascript function.
    
    Allows getting access to the original Python code and the JS code. Also
    allows calling the JS function from Python.
    """
    
    def __init__(self, name, code):
        self._name = name
        self._pycode = code
        
        # Convert to JS, but strip function name, 
        # so that string starts with "function ( ..."
        node = ast.parse(code)
        p = JSParser(node)
        p._parts[0] = 'function' + p._parts[0].split('function', 1)[1]
        self._jscode = p.dump()
    
    def __call__(self, *args):
        #raise RuntimeError('This is a JavaScript function.')
        eval = self.get_app()._exec
        a = ', '.join([repr(arg) for arg in args])
        eval('zoof.widgets.%s.%s("self", %s)' % (self._ob.id, self._name, a))
    
    @property
    def pycode(self):
        return self._pycode
    
    @property
    def jscode(self):
        return self._jscode
    
    # @property
    # def ast(self):
    #     return self._ast
    
    def __repr__(self):
        return '<JSFunction (print to see code) at 0x%x>' % id(self)
    
    def __str__(self):
        pytitle = '== Python code that defined this function =='
        jstitle = '== JS Code that represents this function =='
        return pytitle + '\n' + self.pycode + '\n' + jstitle + self.jscode


def js(func):
    """ Decorate a function with this to make it a JavaScript function.
    
    The decorated function is replaced by a function that you can call to
    invoke the JavaScript function in the web runtime.
    
    The returned function has a ``js`` attribute, which is a JSFunction
    object that can be used to get access to Python and JS code.
    """
    # todo: if function consists of multi-line string, just use that as the JS code
    lines, linenr = inspect.getsourcelines(func)
    indent = len(lines[0]) - len(lines[0].lstrip())
    lines = [line[indent:] for line in lines]
    code = ''.join(lines[1:])
    
    def caller(self, *args):
        eval = self.get_app()._exec
        args = ['self'] + list(args)  # todo: remove self?
        a = ', '.join([repr(arg) for arg in args])
        eval('zoof.widgets.%s.%s(%s)' % (self.id, func.__name__, a))
        
    
    caller.js = JSFuction(func.__name__, code)
    
    return caller
    #return lambda *x, **y: print('This is a JS func')


def py2js(code):
    node = ast.parse(code)
    parser = JSParser(node)
    return parser.dump()


def unify(x):
    """ Turn string or list of strings parts into string. Braces are
    placed around it if its not alphanumerical
    """
    if isinstance(x, (tuple, list)):
        x = ''.join(x)
    if not x.isalnum():
        return '(%s)' % x
    return x


class JSParser:
    """ Transcompile Python to JS.
    This does not intend to support the full Python stack on JS. It is
    more a way to write JS with a Pythonesque syntax. Like Coffeescript,
    it's just JavaScript!
    
    The purpose is to allow definition of JS code inside your Python
    code. No need to learn another language.
    """
    
    COMMON_METHODS = dict(append='push')
    
    NAME_MAP = {
        'self': 'this',
        'True': 'true',
        'False': 'false',
        'None': 'null',
    }
    
    BINARY_OP = {
        'Add'    : '+',
        'Sub'    : '-',
        'Mult'   : '*',
        'Div'    : '/',
        'Mod'    : '%',
        'LShift' : '<<',
        'RShift' : '>>',
        'BitOr'  : '|',
        'BitXor' : '^',
        'BitAnd' : '&',
    }
    
    UNARY_OP = {
        'Invert' : '~',
        'Not'    : '!',
        'UAdd'   : '+',
        'USub'   : '-',
    }
    
    BOOL_OP = {
        'And'    : '&&',
        'Or'     : '||',
    }

    # todo: I think == should become ===, or not? Does JS have identity comp?
    COMP_OP = {
            'Eq'    : "==",
            'NotEq' : "!=",
            'Lt'    : "<",
            'LtE'   : "<=",
            'Gt'    : ">",
            'GtE'   : ">=",
            'Is'    : "===",
            'IsNot' : "!==", # Not implemented yet
        }
    
    def __init__(self, node):
        self._root = node
        self._stack = []
        self._indent = 0
        self._dummy_counter = 0
        
        # Collect function and method handlers
        self._functions, self._methods = {}, {}
        for name in dir(self.__class__):
            if name.startswith('function_'):
                self._functions[name[9:]] = getattr(self, name)
            elif name.startswith('method_'):
                self._methods[name[7:]] = getattr(self, name)
        
        # Parse
        self._push_stack()
        self._parts = self.parse(node)
        if self._parts:
            self._parts[0] = self._parts[0].lstrip()
    
    def _push_stack(self):
        self._stack.append(set())
    
    def _pop_stack(self):
        self._stack.pop(-1)
    
    @property
    def vars(self):
        return self._stack[-1]
    
    def dump(self):
        """ Dumpt the JS code.
        """
        return ''.join(self._parts)
    
    def lf(self, code=''):
        """ Line feed - create a new line with the correct indentation.
        """
        return '\n' + self._indent * '    ' + code
        
    def dummy(self, name=''):
        """ Get a unique name.
        """
        self._dummy_counter += 1
        return 'dummy%i_%s' % (self._dummy_counter, name)
        
    def parse(self, node):
        """ Parse a node. Check node type and dispatch to one of the
        specific parse functions. Raises error if we cannot parse this
        type of node. 
        
        Returns a list of strings.
        """
        nodeType = node.__class__.__name__
        parse_func = getattr(self, 'parse_' + nodeType, None)
        if parse_func:
            res = parse_func(node)
            # Return as list also if a tuple or string was returned
            assert res is not None
            if isinstance(res, tuple):
                res = list(res)
            if not isinstance(res, list):
                res = [res]
            return res
        else:
            raise JSError('Cannot parse %s nodes yet' % nodeType)
    
    ## Literals
    
    def parse_Num(self, node):
        return repr(node.n)
    
    def parse_Str(self, node):
        return repr(node.s)
    
    def parse_Bytes(self, node):
        raise JSError('No Bytes in JS')
    
    def parse_NameConstant(self, node):
        # Py3k
        M = {True: 'true', False: 'false', None: 'null'}
        return M[node.value]
    
    def parse_List(self, node):
        code = ['[']
        for child in node.elts:
            code += self.parse(child)
            code.append(', ')
        if node.elts:
            code.pop(-1)  # skip last comma
        code.append(']')
        return code
    
    def parse_Tuple(self, node):
        return self.parse_List()  # tuple = ~ list in JS
    
    def parse_Dict(self, node):
        code = ['{']
        for key, val in zip(node.keys, node.values):
            code += self.parse(key)
            code.append(': ')
            code += self.parse(val)
            code.append(', ')
        if node.keys:
            code.pop(-1)  # skip last comma
        code.append('}')
        return code
        
    def parse_Set(self, node):
        raise JSError('No Set in JS')
    
    ## Variables
    
    def parse_Name(self, node):
        id = node.id
        id = self.NAME_MAP.get(id, id)
        
        #if id in self.builtin:  -> max, min, sum
        #    id = "py_builtins." + id;
        # todo: ctx Load, Store, Del?
        # todo: implement min, max, sum
        return id
      
    def parse_arg(self, node):
        # Py3k only
        name = node.arg
        return self.NAME_MAP.get(name, name)
    
    def parse_Starred(self, node):
        raise JSError('Starred args are not supported.')
    
    ## Expressions
    
    def parse_Expr(self, node):
        """ Expression (not stored in a variable) """
        code = [self.lf()]
        code += self.parse(node.value)
        code.append(';')
        return code
    
    def parse_UnaryOp(self, node):
        op = self.UNARY_OP[node.op.__class__.__name__]
        right = unify(self.parse(node.operand))
        return '%s%s' % (op, right)
    
    def parse_BinOp(self, node):
        # from py2js
        # if isinstance(node.op, ast.Mod) and isinstance(node.left, ast.Str):
        #     left = self.parse(node.left)
        #     if isinstance(node.right, (ast.Tuple, ast.List)):
        #         right = self.visit(node.right)
        #         return "vsprintf(js(%s), js(%s))" % (left, right)
        #     else:
        #         right = self.visit(node.right)
        #         return "sprintf(js(%s), %s)" % (left, right)
        left = unify(self.parse(node.left))
        right = unify(self.parse(node.right))
        
        if isinstance(node.op, ast.Pow):
            return ["Math.pow(", left, ", ", right, ")"]
        elif isinstance(node.op, ast.FloorDiv):
            return ["Math.floor(", left, "/", right, ")"]
        else:
            op = ' %s ' % self.BINARY_OP[node.op.__class__.__name__]
            return [left, op, right]
    
    def parse_BoolOp(self, node):
        op = ' %s ' % self.BOOL_OP[node.op.__class__.__name__]
        values = [unify(self.parse(val)) for val in node.values]
        return op.join(values)
    
    def parse_Compare(self, node):
        
        # Check
        if len(node.ops) != 1:
            raise JSError('Comparisons with multiple ops is not supported.')
        if len(node.comparators) != 1:
            raise JSError('Comparisons with multiple comps is not supported.')
        
        opnode = node.ops[0]
        comp = node.comparators[0]
        op = self.COMP_OP[opnode.__class__.__name__]
        
        if isinstance(op, ast.In):
            raise JSError('The "in" operator is currently not supported.')
        elif isinstance(op, ast.NotIn):
            raise JSError('The "in" operator is currently not supported.')
        
        left = unify(self.parse(node.left))
        right = unify(self.parse(comp))
        return "%s %s %s" % (left, op, right)
    
    def parse_Call(self, node):
        """ A function call """
        
        # Get full function name and method name if it exists
        if isinstance(node.func, ast.Attribute):
            method_name = node.func.attr
            base_name = unify(self.parse(node.func.value))
            full_name = base_name + '.' + method_name
        else:
            method_name = ''
            full_name = unify(self.parse(node.func))
        
        # Create list of args - keep as parts: each element is a list
        args = [self.parse(arg) for arg in node.args]
        argswithcommas = []
        for arg in args:
            argswithcommas.extend(arg)
            argswithcommas.append(', ')
        if argswithcommas:
            argswithcommas.pop(-1)
        
        # Handle special functions and methods
        res = None
        if method_name in self._methods:
            res = self._methods[method_name](node, full_name, argswithcommas)
        elif full_name in self._functions:
            res = self._functions[full_name](node, full_name, argswithcommas)
        if res is not None:
            return res
        
        # Check for keywords (not supported) after handling special functions
        if node.keywords:
            raise JSError('function calls do not support keyword arguments')
        if node.kwargs:
            raise JSError('function calls do not support **kwargs')
        
        if node.starargs:
            # Func with star args
            if '(' in full_name:
                raise JSError('Function call only supports *args if used on '
                              'a plain object.')
            starname = ''.join(self.parse(node.starargs))
            code = []
            if method_name:
                code += [base_name, '.apply(', base_name, ', [']
            else:
                code += [full_name, '.apply(null, [']
            code += argswithcommas
            code += ['].concat(', starname, '))']
            return code
        else:
            # Normal func
            return [full_name, "("] + argswithcommas + [")"]
    
    def parse_IfExp(self, node):
        # in "a if b else c"
        a = self.parse(node.body)
        b = self.parse(node.test)
        c = self.parse(node.orelse)
        
        code = []
        code.append('(')
        code += b
        code.append(')? (')
        code += a
        code.append(') : (')
        code += c
        code.append(')')
        return code
    
    def parse_Attribute(self, node):
        return "%s.%s" % (unify(self.parse(node.value)), node.attr)
    
    ## Statements
    
    def parse_Assign(self, node):
        """ Variable assignment. """
        code = [self.lf()]
        
        # Parse targets
        newvars = []
        for target in node.targets:
            var = ''.join(self.parse(target))
            if isinstance(target, ast.Name):
                if var not in self.vars:
                    self.vars.add(var)
                    newvars.append((var, target))
                code.append(var)
            elif isinstance(target, ast.Attribute):
                code.append(var)
                #js = self.write("%s.__setattr__(\"%s\", %s);" % (self.visit(target.value), str(target.attr), value))
            else:
                raise JSError("Unsupported assignment type")
            code.append(' = ')
        
        # Take care of new variables
        if len(newvars) == 1:
            code.insert(1, 'var ')
        elif len(newvars) > 1:
            names = [v[0] for v in newvars]
            code.insert(0, 'var ' + ', '.join(names) + ';')
            code.insert(0, self.lf())
        
        # Parse right side
        code += self.parse(node.value)
        code.append(';')
        return code
    
    def visit_Assign(self, node):
        assert len(node.targets) == 1
        target = node.targets[0]
        #~ if self._class_name:
            #~ target = self._class_name + '.' + target
        value = self.visit(node.value)
        if isinstance(target, (ast.Tuple, ast.List)):
            dummy = self.new_dummy()
            self.write("var %s = %s;" % (dummy, value))

            for i, target in enumerate(target.elts):
                var = self.visit(target)
                declare = ""
                if isinstance(target, ast.Name):
                    if not (var in self._scope):
                        self._scope.append(var)
                        declare = "var "
                self.write("%s%s = %s.__getitem__(%d);" % (declare,
                    var, dummy, i))
        elif isinstance(target, ast.Subscript) and isinstance(target.slice, ast.Index):
            # found index assignment
            self.write("%s.__setitem__(%s, %s);" % (self.visit(target.value),
                self.visit(target.slice), value))
        elif isinstance(target, ast.Subscript) and isinstance(target.slice, ast.Slice):
            # found slice assignmnet
            self.write("%s.__setslice__(%s, %s, %s);" % (self.visit(target.value),
                self.visit(target.slice.lower), self.visit(target.slice.upper),
                value))
        else:
            var = self.visit(target)
            if isinstance(target, ast.Name):
                if not (var in self._scope):
                    self._scope.append(var)
                    declare = "var "
                else:
                    declare = ""
                self.write("%s%s = %s;" % (declare, var, value))
            elif isinstance(target, ast.Attribute):
                js = self.write("%s.__setattr__(\"%s\", %s);" % (self.visit(target.value), str(target.attr), value))
            else:
                raise JSError("Unsupported assignment type")
    
    def parse_AugAssign(self, node):  # -> x += 1
        target = ''.join(self.parse(node.target))
        value = ''.join(self.parse(node.value))
        
        nl = self.lf()
        if isinstance(node.op, ast.Pow):
            return [nl, target, " = Math.pow(", target, ", ", value, ")"]
        elif isinstance(node.op, ast.FloorDiv):
            return [nl, target, " = Math.floor(", target, "/", value, ")"]
        else:
            op = ' %s= ' % self.BINARY_OP[node.op.__class__.__name__]
            return [nl, target, op, value]
    
    # parse_Raise
    
    # parse_Assert
    
    # parse_Delete
    
    def parse_Pass(self, node):
        return []
    
    ## Control flow
    
    def parse_If(self, node):
        code = [self.lf('if (')]
        code += self.parse(node.test)
        code.append(') {')
        self._indent += 1
        for stmt in node.body:
            code += self.parse(stmt)
        self._indent -= 1
        if node.orelse:
            code.append("} else {")
            self._indent += 1
            for stmt in node.orelse:
                code += self.parse(stmt)
            self._indent -= 1
        code.append(self.lf("}"))
        return code

        
    def parse_For(self, node):
        
        iter = ''.join(self.parse(node.iter))
        
        # Get target
        sure_is_dict = False  # flag to indicate that we're sure iter is a dict
        if isinstance(node.target, ast.Name):
            target = node.target.id
            target2 = None
            if iter.endswith('.keys()'):
                sure_is_dict = True
                iter = iter.rsplit('.', 1)[0]
            if iter.endswith('.values()'):
                sure_is_dict = True
                iter = iter.rsplit('.', 1)[0]
                target2 = target
        elif isinstance(node.target, ast.Tuple):
            if len(node.target.elts) == 2 and iter.endswith('.items()'):
                sure_is_dict = True
                target = ''.join(self.parse(node.target.elts[0]))
                target2 = ''.join(self.parse(node.target.elts[1]))
                iter = iter.rsplit('.', 1)[0]  # strip ".iter()"
            else:
                raise JSError('Only one iterator allowed in for-loop, '
                              'or 2 when using .items()')
        else:
            raise JSError('Invalid iterator in for-loop')
        
        # Collect body and else-body
        for_body = []
        for_else = []
        self._indent += 1
        for n in node.body:
            for_body += self.parse(n)
        for n in node.orelse:
            for_else += self.parse(n)
        self._indent -= 1
        
        # Init code
        code = []
        
        # Prepare variable to detect else
        if node.orelse:
            else_dummy = self.dummy('else')
            code.append(self.lf('var %s = true;' % else_dummy))
        
        # Declare iteration variable if necessary
        if target not in self.vars:
            self.vars.add(target)
            code.append(self.lf('var %s;' % target))
        if target2 and target2 not in self.vars:
            self.vars.add(target2)
            code.append(self.lf('var %s;' % target2))
        
        if iter.startswith('range('):  # Explicit iteration 
            # Get range args
            args = iter.split('(', 1)[1].rsplit(')', 1)[0]
            nums = [x.strip() for x in args.split(',')]
            assert len(nums) in (1, 2, 3)
            if len(nums) == 1:
                start, end, step = '0', nums[0], '1'
            elif len(nums) == 2:
                start, end, step = nums[0], nums[1], '1'
            elif len(nums) == 3:
                start, end, step = nums[0], nums[1], nums[2]
            # Build for-loop in JS
            t = 'for ({i} = {start}; {i} < {end}; {i} += {step})'
            if step.lstrip('+-').isnumeric() and float(step) < 0:
                t = t.replace('<', '>')
            t = t.format(i=target, start=start, end=end, step=step) + ' {'
            code.append(self.lf(t))
            self._indent += 1
        
        elif sure_is_dict:  # Enumeration over an object (i.e. a dict)
            # Create dummy vars
            d_seq = self.dummy('sequence')
            code.append(self.lf('var %s = %s;' % (d_seq, iter)))
            # The loop
            code += self.lf(), 'for (', target, ' in ', d_seq, ') {'
            self._indent += 1
            code.append(self.lf('if (!%s.hasOwnProperty(%s)){ continue; }' % 
                                (d_seq, target)))
            # Set second/alt iteration variable
            if target2:
                code.append(self.lf('%s = %s[%s];' % (target2, d_seq, target)))
        
        else:  # Enumeration 
        
            # We cannot know whether the thing to iterate over is an
            # array or a dict. We use a for-iterarion (otherwise we
            # cannot be sure of the element order for arrays). Before
            # running the loop, we test whether its an array. If its
            # not, we replace the sequence with the keys of that
            # sequence. Peformance for arrays should be good. For
            # objects probably slightly less.
            
            # Create dummy vars
            d_seq = self.dummy('sequence')
            d_iter = self.dummy('iter')
            d_len = self.dummy('length')
            code.append(self.lf('var %s, %s, %s = %s;' % 
                                (d_iter, d_len, d_seq, iter)))
            
            # Replace sequence with dict keys if its a dict
            # Note that Object.keys() only yields own enumerable properties
            code.append(self.lf('if ((typeof %s === "object") && '
                                '(!Array.isArray(%s))) {' % (d_seq, d_seq)))
            
            code.append(self.lf('    var %s = Object.keys(%s);' % 
                                (d_seq, d_seq)))
            code.append(self.lf('}'))
            
            # The loop
            code.append(self.lf('%s = %s.length;' % (d_len, d_seq)))
            code.append(self.lf('for (%s = 0; %s < %s; %s += 1) {' % 
                                (d_iter, d_iter, d_len, d_iter)))
            self._indent += 1
            code.append(self.lf('%s = %s[%s];' % (target, d_seq, d_iter)))
        
        # The body of the loop
        code += for_body
        self._indent -= 1
        code.append(self.lf('}'))
        
        # Handle else
        if node.orelse:
            code.append(' if (%s) {' % else_dummy)
            code += for_else
            code.append(self.lf("}"))
            # Update all breaks to set the dummy. We overwrite the
            # "break;" so it will not be detected by a parent loop
            ii = [i for i, part in enumerate(code) if part=='break;']
            for i in ii:
                code[i] = '%s = false; break;' % else_dummy
        
        return code
    
    def parse_While(self, node):
        
        test = ''.join(self.parse(node.test))
        
        # Collect body and else-body
        for_body = []
        for_else = []
        self._indent += 1
        for n in node.body:
            for_body += self.parse(n)
        for n in node.orelse:
            for_else += self.parse(n)
        self._indent -= 1
        
        # Init code
        code = []
        
        # Prepare variable to detect else
        if node.orelse:
            else_dummy = self.dummy('else')
            code.append(self.lf('var %s = true;' % else_dummy))
        
        # The loop itself
        code.append(self.lf("while (%s) {" % test))
        self._indent += 1
        code += for_body
        self._indent -= 1
        code.append(self.lf('}'))
        
        # Handle else
        if node.orelse:
            code.append(' if (%s) {' % else_dummy)
            code += for_else
            code.append(self.lf("}"))
            # Update all breaks to set the dummy. We overwrite the
            # "break;" so it will not be detected by a parent loop
            ii = [i for i, part in enumerate(code) if part=='break;']
            for i in ii:
                code[i] = '%s = false; break;' % else_dummy
        
        return code
    
    def parse_Break(self, node):
        # Note that in parse_For, we detect breaks and modify them to
        # deal with the for-else clause
        return [self.lf(), 'break;']
    
    def parse_Continue(self, node):
        return self.lf('continue;')
    
    #def parse_Try
    #def parse_TryFinally
    #def parse_ExceptHandler
    
    #def parse_With
    #def parse_Withitem
    
    ## Functions and class definitions
    
    def parse_FunctionDef(self, node):
        """ A function definition """
        
        code = [self.lf('var %s = function (' % node.name)]
        
        # Collect args
        argnames = []
        for arg in node.args.args:
            if not isinstance(arg, (ast.arg, ast.Name)):
                raise JSError("tuples in argument list are not supported")
            name = ''.join(self.parse(arg))
            if name != 'this':
                argnames.append(name)
                # Add code and comma
                code.append(name)
                code.append(', ')
        if argnames:
            code.pop(-1)  # pop last comma
        
        # Check
        if node.decorator_list:
            raise JSError('No support for decorators')
        if node.args.kwonlyargs:
            raise JSError('No support for keyword only arguments')
        if node.args.kwarg:
            raise JSError('No support for kwargs')
        
        # Prepare for content
        code.append(') {')
        self._indent += 1
        
        # Apply defaults
        offset = len(argnames) - len(node.args.defaults)
        for name, default in zip(argnames[offset:], node.args.defaults):
            x = '%s = %s || %s;' % (name, name, ''.join(self.parse(default)))
            code.append(self.lf(x))
        
        # Handle varargs
        if node.args.vararg:
            asarray = 'Array.prototype.slice.call(arguments)'
            name = node.args.vararg.arg
            if not argnames:
                # Make available under *arg name
                #code.append(self.lf('var %s = arguments;' % name))
                code.append(self.lf('var %s = %s;' % (name, asarray)))
            else:
                # Slice it
                code.append(self.lf('var %s = %s.slice(%i);' % 
                            (name, asarray, len(argnames))))
        # Apply content
        for child in node.body:
            code += self.parse(child)
        
        # Wrap up
        self._indent -= 1
        code.append(self.lf('};'))
        return code
    
    def _functiondef(self, node):
        is_static = False
        is_javascript = False
        if node.decorator_list:
            if len(node.decorator_list) == 1 and \
                    isinstance(node.decorator_list[0], ast.Name) and \
                    node.decorator_list[0].id == "JavaScript":
                is_javascript = True  # this is our own decorator
            elif self._class_name and \
                    len(node.decorator_list) == 1 and \
                    isinstance(node.decorator_list[0], ast.Name) and \
                    node.decorator_list[0].id == "staticmethod":
                is_static = True
            else:
                raise JSError("decorators are not supported")

        # XXX: disable $def for now, because it doesn't work in IE:
        
        else:
            defaults = [None]*(len(node.args.args) - len(node.args.defaults)) + node.args.defaults

            args = []
            defaults2 = []
            for arg, default in zip(node.args.args, defaults):
                if not isinstance(arg, ast.Name):
                    raise JSError("tuples in argument list are not supported")
                if default:
                    defaults2.append("%s: %s" % (arg.id, self.visit(default)))
                args.append(arg.id)
            defaults = "{" + ", ".join(defaults2) + "}"
            args = ", ".join(args)
            self.write("var %s = $def(%s, function(%s) {" % (node.name,
                defaults, args))
            self._scope = [arg.id for arg in node.args.args]
            self.indent()
            for stmt in node.body:
                self.visit(stmt)
            self.dedent()
            self.write("});")
    
    #def parse_Lambda
    
    def parse_Return(self, node):
        if node.value is not None:
            code = [self.lf('return ')]
            code += self.parse(node.value)
            code.append(';')
            return code
        else:
            return self.lf("return;")
    
    #def parse_Yield
    #def parse_YieldFrom
    #def parse_Global
    #def parse_NonLocal
    #def parse_ClassDef 
    
    ## Subscripting
    
    def parse_Subscript(self, node):
        code = self.parse(node.value)
        
        if isinstance(node.slice, ast.Index):
            code.append('[')
            code += self.parse(node.slice.value)
            code.append(']') 
        else:
            code.append('.slice(')
            code += self.parse(node.slice)
            code.append(')')
        return code
    
    def parse_Index(self, node):
        return self.parse(node.value)
    
    def parse_Slice(self, node):
        code = []
        if node.step:
            raise JSError('Slicing with step not supported.')
        if node.lower:
            code += self.parse(node.lower)
        else:
            code.append('0')
        if node.upper:
            code.append(',')
            code += self.parse(node.upper)
        return code 
    
    def parse_ExtSlice(self, node):
        raise JSError('Multidimensional slicing not supported in JS')
    
    ## Comprehensions
    
    # ListComp
    # SetComp
    # GeneratorExp
    # DictComp
    # comprehension
    
    ## Imports - no imports

    # parse_Import
    # parse_ImportFrom
    # parse_alias
    
    def parse_Module(self, node):
        """ Module level. Just skip. """
        code = []
        for child in node.body:
            code += self.parse(child)
        return code
    
    
    ## Functions and methods that we handle specifically
    
    def function_print(self, node, func, args):
        # Process keywords
        sep, end = '" "', ''
        for kw in node.keywords:
            if kw.arg == 'sep':
                sep = ''.join(self.parse(kw.value))
            elif kw.arg == 'end':
                end = ''.join(self.parse(kw.value))
            elif kw.arg in ('file', 'flush'):
                raise JSError('print() file and flush args not supported')
            else:
                raise JSError('Invalid argument for print(): %r' % kw.arg)
        
        # Combine args
        args = [unify(self.parse(arg)) for arg in node.args]
        end = (" + %s" % end) if (args and end and end != '\n') else ''
        combiner = ' + %s + ' % sep
        args_concat = combiner.join(args)
        return 'console.log(' + args_concat + end + ')'
    
    def function_len(self, node, func, args):
        if len(args) == 1:
            return unify(args[0]), '.length'
    
    def method_append(self, node, func, args):
        base, method = func.rsplit('.', 1)
        code = []
        code.append('(%s.append || %s.push).apply(%s, [' % (base, base, base))
        code += args
        code.append('])')
        return code


if __name__ == '__main__':
    
    
    print(py2js('foo(a, b, *c)'))
    print(py2js('foo.bar(a, b, *c)'))
    
    
    1/0
    
    @js
    def t_func():
        2
    
    class Foo:
        @js
        def bar(self, bar, spam=4, *more):
            __SIMPLE_TYPES__
            foo = 'hello'
            foo = [1, 2]
            foo.append(3)
            __ATTRIBUTES__
            foo.bar = 'asd'
            __PRINTING_AND_FORMATTING__
            print(spam, 'world!', 5., [1,2,3])
    
    
    foo = Foo()
    #print(dump(foo.bar))
    
    print('----')
    # for node in ast.walk(foo.bar):
    #     print(node)
    print(foo.bar.js)
    