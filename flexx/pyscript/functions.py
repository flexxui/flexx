from types import FunctionType
import inspect
import subprocess

from .pythonicparser import PythonicParser


def py2js(code):
    """ Translate Python code to JavaScript.
    """
    parser = PythonicParser(code)
    return parser.dump()


def evaljs(code, whitespace=True):
    """ Evaluate JavaScript code in Node.js. 
    
    Return last result as a string. If whitespace is False, the whitespace
    is stripped removed from the result.
    """
    res = subprocess.check_output(['nodejs', '-p', '-e', code])
    res = res.decode().rstrip()
    if res.endswith('undefined'):
        res = res[:-9].rstrip()
    if not whitespace:
        res = res.replace('\n', '').replace('\t', '').replace(' ', '')
    return res


def evalpy(code, whitespace=True):
    """ Evaluate PyScript code in Node.js (after translating to JS).
    
    Return last result as a string. If whitespace is False, the whitespace
    is stripped removed from the result.
    """
    return evaljs(py2js(code), whitespace)


def js(func):
    """ Turn a function into a JavaScript function, usable as a decorator.
    
    The given function is replaced by a function that you can call to
    invoke the JavaScript function in the web runtime.
    
    The returned function has a ``js`` attribute, which is a JSFunction
    object that can be used to get access to Python and JS code.
    """
    
    if isinstance(func, JSFunction):
        return func
    if not isinstance(func, FunctionType):
        raise ValueError('The js decorator only accepts real functions.')
    
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
    lines, linenr = inspect.getsourcelines(func)
    indent = len(lines[0]) - len(lines[0].lstrip())
    lines = [line[indent:] for line in lines]
    if lines[0].startswith('@'):
        code = ''.join(lines[1:])  # decorated function
    else:
        code = ''.join(lines)  # function object explicitly passed to js()
    
    # def caller(self, *args):
    #     eval = self.get_app()._exec
    #     args = ['self'] + list(args)  # todo: remove self?
    #     a = ', '.join([repr(arg) for arg in args])
    #     eval('flexx.widgets.%s.%s(%s)' % (self.id, name, a))
    # 
    # caller.js = JSFunction(name, code)
    
    return JSFunction(name, code)


class JSFunction(object):
    """ Placeholder for storing the original Python code and the JS code.
    """
    
    def __init__(self, name, code):
        self._name = name
        self._pycode = code
        
        # Convert to JS, but strip function name, 
        # so that string starts with "function ( ..."
        p = PythonicParser(code)
        p._parts[0] = ''  # remove "var xx = "
        self._jscode = p.dump()
        assert self._jscode.startswith('function')
    
    @property
    def name(self):
        return self._name
    
    @property
    def pycode(self):
        return self._pycode
    
    @property
    def jscode(self):
        return self._jscode
    
    def __call__(self, *args, **kwargs):
        raise RuntimeError('Cannot call a JS function directly from Python')
    
    def __repr__(self):
        return '<JSFunction (print to see code) at 0x%x>' % id(self)
    
    def __str__(self):
        pytitle = '== Python code that defined this function =='
        jstitle = '== JS Code that represents this function =='
        return pytitle + '\n' + self.pycode + '\n' + jstitle + self.jscode
