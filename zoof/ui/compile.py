"""

Parts of this code are inspired by / taken from the py2js project.


Supported:

* numbers, strings
* print function (no ``end`` and ``sep`` though)
* multiple assignment
* lists (becomes JS array)
* tuple (becomes JS array)
* dicts (becomes JS objects)
* function calls
* function defs can have *args
* calling a function with keyword args (are passed via an object arg)
* Power and integer division operators

Not currently supported:

* tuple packing/unpacking
* function defs cannot have ``**kwargs``
* cannot call a function with ``*args``

Probably never suppored:

* Most Python buildins
* importing


"""

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
        #'print': 'console.log',  # handled explicitly, also args
        #'int': '_int',
        #'float': '_float',
        #'py_builtins' : '___py_hard_to_collide',
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

    COMP_OP = {
            'Eq'    : "==",
            'NotEq' : "!=",
            'Lt'    : "<",
            'LtE'   : "<=",
            'Gt'    : ">",
            'GtE'   : ">=",
            'Is'    : "===",
            'IsNot' : "is not", # Not implemented yet
        }
    
    def __init__(self, node):
        self._root = node
        # self._js = []
        self._stack = []
        self._indent = 0
        self._push_stack()
        self._parts = self.parse(node)
        if self._parts:
            self._parts[0] = self._parts[0].lstrip()
    
    def _push_stack(self):
        self._stack.append({})
    
    def _pop_stack(self):
        self._stack.pop(-1)
    
    @property
    def vars(self):
        return list(self._stack[-1].keys())
    
    
    # def write(self, code):
    #     self._js.append(code)
    # 
    # def writeline(self, code):
    #     self._js.append('\n' + self._indent * '    ' + code)
    # 
    # def unwrite(self, count=1):
    #     for i in range(count):
    #         self._js.pop(-1)
    
    def dump(self):
        """ Dumpt the JS code.
        """
        return ''.join(self._parts)
        #code = ''.join(self._js)
        #return code.strip() + '\n'
    
    def newline(self, code=''):
        return '\n' + self._indent * '    ' + code
        
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
        # todo: was this py2k or py3k?
        name = node.arg
        return self.NAME_MAP.get(name, name)
    
    # def parse_Starred 
    
    ## Expressions
    
    def parse_Expr(self, node):
        """ Expression (not stored in a variable) """
        code = [self.newline()]
        code += self.parse(node.value)
        code.append(';')
        return code
    
    # def parse_UnaryOp
    
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
        left = ''.join(self.parse(node.left))
        right = ''.join(self.parse(node.right))

        if isinstance(node.op, ast.Pow):
            return ["Math.pow(", left, ", ", right, ")"]
        elif isinstance(node.op, ast.FloorDiv):
            return ["Math.floor(", left, "/", right, ")"]
        else:
            op = ' %s ' % self.BINARY_OP[node.op.__class__.__name__]
            return [left, op, right]
    
    # def parse_BoolOp
    # def parse_Compare
    
    def parse_Call(self, node):
        """ A function call """
        func = self.parse(node.func)
        
        # Create list of args - keep as parts: each element is a list
        args = [self.parse(arg) for arg in node.args]
        
        # kwargs are passed as a dict (as one extra argument)
        if node.keywords:
            keywords = []
            for kw in node.keywords:
                val = ''.join(self.parse(kw.value))
                keywords.append("%s: %s" % (kw.arg, val))
            args.append(["{" + ", ".join(keywords) + "}"])
        
        if func[0] == 'print':
            # Deal with print function
            if node.keywords:
                raise JSError('Cannot use kwargs with print().')
            args = [''.join(arg) for arg in args]
            if len(args) > 1:
                args = ['(%s)' % arg for arg in args]
            args_concat = ' + " " + '.join(args)
            return 'console.log(' + args_concat + ')'
        
        else:
            # Normal func
            argswithcommas = []
            for arg in args:
                argswithcommas.extend(arg)
                argswithcommas.append(', ')
            if argswithcommas:
                argswithcommas.pop(-1)
            return func + ["("] + argswithcommas + [")"]
    
    # def parse_IfExp
    
    def parse_Attribute(self, node):
        return "%s.%s" % (''.join(self.parse(node.value)), node.attr)
    
    
    ## Statements
    
    def parse_Assign(self, node):
        """ Variable assignment. """
        code = [self.newline()]
        
        # Parse targets
        newvars = []
        for target in node.targets:
            var = ''.join(self.parse(target))
            if isinstance(target, ast.Name):
                if var not in self.vars:
                    newvars.append((var, target))
                code.append(var)
            elif isinstance(target, ast.Attribute):
                code.append(var)
                #js = self.write("%s.__setattr__(\"%s\", %s);" % (self.visit(target.value), str(target.attr), value))
            else:
                raise JSError("Unsupported assignment type")
            code.append(' = ')
        
        # Take care of new variables
        for var, target in newvars:
            self._stack[-1][var] = node.value
        if len(newvars) == 1:
            code.insert(1, 'var ')
        elif len(newvars) > 1:
            names = [v[0] for v in newvars]
            code.insert(0, 'var ' + ', '.join(names) + ';')
            code.insert(0, self.newline())
        
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
                
    # parse_AugAssign   -> x += 1
    # parse_Raise
    # parse_Assert
    # parse_Delete
    
    def parse_Pass(self, node):
        return []
    
    
    ## Control flow
    
    def parse_If(self, node):
        code = ['if (']
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
        code.append(self.newline("}"))
        return code

        
    #def parse_For
    #def parse_While
    #def parse_Break
    #def parse_Continue
    
    #def parse_Try
    #def parse_TryFinally
    #def parse_ExceptHandler
    
    #def parse_With
    #def parse_Withitem
    
    ## Functions and class definitions
    
    def parse_FunctionDef(self, node):
        """ A function definition """
        
        code = [self.newline('var %s = function (' % node.name)]
        
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
        # todo: keyword arguments follow same procedure as in parse_call
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
            code.append(self.newline(x))
        
        # Handle varargs
        if node.args.vararg:
            asarray = 'Array.prototype.slice.call(arguments)'
            name = node.args.vararg.arg
            if not argnames:
                # Make available under *arg name
                #code.append(self.newline('var %s = arguments;' % name))
                code.append(self.newline('var %s = %s;' % (name, asarray)))
            else:
                # Slice it
                code.append(self.newline('var %s = %s.slice(%i);' % 
                            (name, asarray, len(argnames))))
        # Apply content
        for child in node.body:
            code += self.parse(child)
        
        # Wrap up
        self._indent -= 1
        code.append(self.newline('};'))
        return code
    
    def _functiondef(self, node):
        is_static = False
        is_javascript = False
        if node.decorator_list:
            if len(node.decorator_list) == 1 and \
                    isinstance(node.decorator_list[0], ast.Name) and \
                    node.decorator_list[0].id == "JavaScript":
                is_javascript = True # this is our own decorator
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
            code = [self.newline('return ')]
            code += self.parse(node.value)
            code.append(';')
            return code
        else:
            return self.newline("return;")
    
    #def parse_Yield
    #def parse_YieldFrom
    #def parse_Global
    #def parse_NonLocal
    #def parse_ClassDef 
    
    
    ## Subscripting
    
    # ...
    
    ## Comprehensions
    
    # ...
    
    def parse_Module(self, node):
        """ Module level. Just skip. """
        code = []
        for child in node.body:
            code += self.parse(child)
        return code
    
    ## Imports - no imports


if __name__ == '__main__':
    
    print(py2js('foo.bar = 2'))
    
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
    