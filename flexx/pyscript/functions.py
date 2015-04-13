import ast
import types
import inspect
import ast
import subprocess

from .pythonicparser import PythonicParser


def py2js(code):
    """ Translate Python code to JavaScript.
    """
    node = ast.parse(code)
    parser = PythonicParser(node)
    return parser.dump()


def evaljs(code, whitespace=True):
    """ Evaluate code in Node.js. Return last result as a string.
    """
    res = subprocess.check_output(['nodejs', '-p', '-e', code])
    res = res.decode().rstrip()
    if res.endswith('undefined'):
        res = res[:-9].rstrip()
    if not whitespace:
        res = res.replace('\n', '').replace('\t', '').replace(' ', '')
    return res


def evalpy(code, whitespace=True):
    """ Evaluate python code in Node.js (after translating to js).
    """
    return evaljs(py2js(code), whitespace)


def js(func):
    """ Decorate a function with this to make it a JavaScript function.
    
    The decorated function is replaced by a function that you can call to
    invoke the JavaScript function in the web runtime.
    
    The returned function has a ``js`` attribute, which is a JSFunction
    object that can be used to get access to Python and JS code.
    """
    if not isinstance(func, types.FunctionType):
        raise ValueError('The js decorator can only decorate real functions.')
    
    # Get name - strip "__js" suffix if it's present
    # This allow mangling the function name on the Python side, to allow
    # the same name for a function in both Py and JS. I investigated
    # other solutions, from class-inside-class constructions to
    # black-magic decorators that auto-mangle the function name. I settled
    # on just allowing "func_name__js".
    name = func.__name__
    if name.endswith('__js'):
        name = name[:-4]
    
    # Get code
    # todo: if function consists of multi-line string, just use that as the JS code
    lines, linenr = inspect.getsourcelines(func)
    indent = len(lines[0]) - len(lines[0].lstrip())
    lines = [line[indent:] for line in lines]
    code = ''.join(lines[1:])
    
    def caller(self, *args):
        eval = self.get_app()._exec
        args = ['self'] + list(args)  # todo: remove self?
        a = ', '.join([repr(arg) for arg in args])
        eval('flexx.widgets.%s.%s(%s)' % (self.id, name, a))
    
    caller.js = JSFunction(name, code)
    
    # todo: should we even allow calling the js function?
    return caller
    #return lambda *x, **y: print('This is a JS func')


class JSFunction:
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
        p = PythonicParser(node)
        p._parts[0] = ''  # remove "var xx = "
        self._jscode = p.dump()
    
    def __call__(self, *args):
        #raise RuntimeError('This is a JavaScript function.')
        eval = self.get_app()._exec
        a = ', '.join([repr(arg) for arg in args])
        eval('flexx.widgets.%s.%s("self", %s)' % (self._ob.id, self._name, a))
    
    @property
    def name(self):
        return self._name
    
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


