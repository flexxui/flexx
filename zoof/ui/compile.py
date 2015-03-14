import inspect
import ast
from astpp import dump, parseprint  # 3d party


class JSFuction:
    def __init__(self, name, code):
        self._name = name
        self._pycode = code
        self._ast = ast.parse(code)
        self._jscode = JSParser(self._ast).dump()
    
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
    
    @property
    def ast(self):
        return self._ast
    
    def __repr__(self):
        return '<JSFunction (print to see JS code) at 0x%x>' % id(self)
    
    def __str__(self):
        pytitle = '== Python code that defined this function =='
        jstitle = '== JS Code that represents this function =='
        return pytitle + '\n' + self.pycode + '\n' + jstitle + self.jscode


def js(func):
    """ Decorator
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



class JSParser:
    """ Transcompile Python to JS.
    This does not intend to support the full Python stack on JS. It is
    more a way to write JS with a Pythonesque syntax. Like Coffeescript:
    it's just JavaScript!
    
    The purpose is to allow definition of JS code inside your Python
    code. No need to learn another language.
    """
    
    COMMON_METHODS = dict(append='push')
    
    def __init__(self, node):
        self._root = node
        self._js = []
        self._stack = []
        self._indent = 0
        self._push_stack()
        self.parse_node(node)
    
    def _push_stack(self):
        self._stack.append({})
    
    def _pop_stack(self):
        self._stack.pop(-1)
    
    @property
    def vars(self):
        return list(self._stack[-1].keys())
        
    def _addjs(self, code):
        self._js.append(code)
    
    def _addjsline(self, code):
        self._js.append('\n' + self._indent * '    ' + code)
    
    def _removejs(self, count=1):
        for i in range(count):
            self._js.pop(-1)
    
    def dump(self):
        """ Dumpt the JS code.
        """
        return ''.join(self._js)
    
    @classmethod
    def py2js(cls, code):
        return css(code).dump()
    
    def parse_node(self, node):
        """ Parse a node. Check node type and dispatch to one of the
        specific parse functions. Raises error if we cannot parse this
        type of node. 
        """
        nodeType = node.__class__.__name__
        parse_func = getattr(self, 'parse_' + nodeType, None)
        if parse_func:
            return parse_func(node)
        else:
            raise NotImplementedError('Cannot parse %s nodes yet' % nodeType)
    
    ## Literals
    
    def parse_Num(self, node):
        self._addjs(repr(node.n))
    
    def parse_Str(self, node):
        self._addjs(repr(node.s))
    
    def parse_Bytes(self, node):
        raise NotImplementedError('No Bytes in JS')
    
    def parse_NameConstant(self, node):
        M = {True: 'true', False: 'false', None: 'null'}
        self._addjs(M[node.value])
    
    def parse_List(self, node):
        self._addjs('[')
        for child in node.elts:
            self.parse_node(child)
            self._addjs(', ')
        self._removejs()
        self._addjs(']')
    
    def parse_Tuple(self, node):
        return self.parse_List()  # tuple = ~ list in JS
    
    def parse_Dict(self, node):
        self._addjs('{')
        for key, val in zip(node.keys, node.values):
            self.parse_node(key)
            self._addjs(': ')
            self.parse_node(val)
            self._addjs(', ')
        self._removejs()
        self._addjs('}')
        
    def parse_Set(self, node):
        raise NotImplementedError('No Set in JS')
    
    ## Variables
    
    def parse_Name(self, node):
        self._addjs(node.id)
        # todo: ctx Load, Store, Del?
    
    # def parse_Starred 
    
    ## Expressions
    
    def parse_Expr(self, node):
        """ Expression (not stored in a variable) """
        self._addjsline('')
        self.parse_node(node.value)
        self._addjs(';')
    
    # def parse_UnaryOp
    # def parse_ BinOp
    # def parse_BoolOp
    # def parse_Compare
    
    def parse_Call(self, node):
        """ A function call """
        self.parse_node(node.func)
        
        # if isinstance(node.func, ast.Name):
        #     name = node.func.id
        #         
        # else:  # Attribute
        #     name = node.func.value.id + '.' + node.func.attr
        name = self._js[-1]
        if name == 'print':
            self._removejs()
            self._addjs('console.log(')
            for arg in node.args:
                self.parse_node(arg)
                self._addjs(' + " " + ')
        else:
            self._addjs('(')
            for arg in node.args:
                self.parse_node(arg)
                self._addjs(', ')
        self._removejs()  # remove last comma
        self._addjs(')')
    
    # def parse_IfExp
    
    def parse_Attribute(self, node):
        self.parse_node(node.value)
        
        attr = node.attr
        alias = self.COMMON_METHODS.get(attr, None)
        if False:#alias:
            name = '.(%s||%s)' % (attr, alias)
        else:
            name = '.' + attr
        self._addjs(name)
    
    
    ## Statements
    
    def parse_Assign(self, node):
        """ Variable assignment. """
        self._addjsline('')
        for name in node.targets:
            if isinstance(name, ast.Name):
                if name.id not in self.vars:
                    self._addjs('var ')
                self._addjs(name.id)
                self._stack[-1][name] = node.value
            else:
                self.parse_node(name)
            self._addjs(' = ')
            
        self.parse_node(node.value)
        self._addjs(';')
    
    # parse_AugAssign   -> x += 1
    # parse_Raise
    # parse_Assert
    # parse_Delete
    
    def parse_Pass(self, node):
        pass  # :)
    
    
    ## Control flow
    
    #def parse_If
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
        self._addjsline('var %s = function (' % node.name)
        # Args
        argnames = [(arg.arg if hasattr(arg, 'arg') else arg.name)
                    for arg in node.args.args]  # py2/py3
        for name in argnames:
            self._addjs(name); self._addjs(', ')
        self._removejs()  # remove last comma
        # Check
        if node.args.kwonlyargs:
            raise NotImplementedError('No support for keyword only arguments')
        if node.args.kwarg:
            raise NotImplementedError('No support for kwargs')
        # Prepare for content
        self._addjs(') {')
        self._indent += 1
        # Apply defaults
        offset = len(argnames) - len(node.args.defaults)
        for name, default in zip(argnames[offset:], node.args.defaults):
            self._addjsline(name + ' ||= ')
            self.parse_node(default)
            self._addjs(';')
        # Handle varargs
        if node.args.vararg:
            self._addjsline(node.args.vararg.arg + ' = ' + 
                            'arguments.slice(%i);' % len(argnames))
        # Apply content
        for child in node.body:
            self.parse_node(child)
        # Wrap up
        self._indent -= 1
        self._addjsline('};')
        
    #def parse_Lambda
    
    #def parse_Return
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
        for child in node.body:
            self.parse_node(child)
    
    
    
    ## Imports - no imports


if __name__ == '__main__':
    class Foo:
        @js
        def bar(self, bar, spam=4, *more):
            foo = 'hello'
            foo = [1, 2]
            foo.append(3)
            foo.bar = 'asd'
            print(spam, 'world!', 5., [1,2,3])
    
    
    foo = Foo()
    #print(dump(foo.bar))
    
    print('----')
    # for node in ast.walk(foo.bar):
    #     print(node)
    print(foo.bar)