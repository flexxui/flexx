from types import FunctionType
import inspect
import subprocess

from .pythonicparser import PythonicParser


def py2js(pycode):
    """ Translate Python code to JavaScript.
    
    parameters:
        pycode (str): the Python code to transalate.
    
    returns:
        jscode (str): the resulting JavaScript.
    """
    parser = PythonicParser(pycode)
    return parser.dump()


def evaljs(jscode, whitespace=True):
    """ Evaluate JavaScript code in Node.js. 
    
    parameters:
        jscode (str): the JavaScript code to evaluate.
        whitespace (bool): if whitespace is False, the whitespace
            is removed from the result.
    
    returns:
        result (str): the last result as a string.
    """
    res = subprocess.check_output(['nodejs', '-p', '-e', jscode])
    res = res.decode().rstrip()
    if res.endswith('undefined'):
        res = res[:-9].rstrip()
    if not whitespace:
        res = res.replace('\n', '').replace('\t', '').replace(' ', '')
    return res


def evalpy(pycode, whitespace=True):
    """ Evaluate PyScript code in Node.js (after translating to JS).
    
    parameters
    ----------
    pycode : str
        the PyScript code to evaluate.
    whitespace : bool
        if whitespace is False, the whitespace is removed from the result.
    
    returns
    -------
    result : str
        the last result as a string.
    """
    # delibirate numpy doc style to see if napoleon handles it the same
    return evaljs(py2js(code), whitespace)


def js(func):
    """ Turn a function into a JavaScript function.
    
    parameters:
        func (function): The function to transtate. If this is a 
            JSFunction object, it is returned as-is.
    
    returns:
        jsfunction (JSFunction): An object that has a ``jscode``
        ``pycode`` and ``name`` attribute.
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
    #     args = ['self'] + list(args)
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
