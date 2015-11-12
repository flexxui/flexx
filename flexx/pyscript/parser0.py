# -*- coding: utf-8
"""
Parts of this code (and in the other modules that define the parser
class) are inspired by / taken from the py2js project.

Useful links:
 * https://greentreesnakes.readthedocs.org/en/latest/nodes.html
 * https://github.com/qsnake/py2js/blob/master/py2js/__init__.py

Known limitations for Browsers. Probably best if we provide a piece of
code that can be executed to add functionality to types for these
situations:
 * Array.indexOf supported from IE 9 - we use it in the In operator
 * Object.keys supported from IE 9 - we use it in method_keys()

"""

import sys
import re

from . import commonast as ast
from . import stdlib


class JSError(Exception):
    """ Exception raised when unable to convert Python to JS.
    """
    pass


def unify(x):
    """ Turn string or list of strings parts into string. Braces are
    placed around it if its not alphanumerical
    """
    # Note that r'[\.\w]' matches anyting in 'ab_01.äé'
    
    if isinstance(x, (tuple, list)):
        x = ''.join(x)
    
    if x[0] in '\'"' and x[0] == x[-1] and x.count(x[0]) == 2:
        return x  # string
    elif re.match(r'^[\.\w]*$', x):
        return x  # words consisting of normal chars, numbers and dots
    elif re.match(r'^[\.\w]*\(.*\)$', x) and x.count(')') == 1:
        return x  # function calls (e.g. 'super()' or 'foo.bar(...)')
    elif re.match(r'^[\.\w]*\[.*\]$', x) and x.count(']') == 1:
        return x  # indexing
    elif re.match(r'^\{.*\}$', x) and x.count('}') == 1:
        return x  # dicts
    else:
        return '(%s)' % x


# https://github.com/umdjs/umd/blob/master/returnExports.js
UMD = """
(function (root, factory) {
    if (typeof define === 'function' && define.amd) {
        // AMD. Register as an anonymous module.
        define([%s], factory);
    } else if (typeof exports !== 'undefined') {
        // Node or CommonJS
        module.exports = factory(%s);
        if (typeof window === 'undefined') {
            root.%s = module.exports;  // also create global module in Node
        }
    } else {
        // Browser globals (root is window)
        root.%s = factory(%s);
    }
}(this, function (%s) {
""".lstrip()  # "dep", require("dep"), name, root.dep, dep


def get_module_preamble(name, deps):
    """ Wrap code in a module compatible with UMD (Universal Module
    Definition), making it work with AMD (i.e. require), Node, plain
    browser.
    
    Parameters:
        name (str): the name of the module
        deps (list): dependency names
    Returns:
        code: a preamble to prepend the actual module code with.
        Don't forget to return the namespace, and put ``}));`` at the end.
    """
    
    dep_strings = ', '.join([repr(dep) for dep in deps])
    dep_requires = ', '.join(['require(%s)' % repr(dep) for dep in deps])
    dep_names = ', '.join(deps)
    dep_fullnames = ', '.join('root.' + dep for dep in deps)
    
    return UMD % (dep_strings, dep_requires, name, name, dep_fullnames, dep_names)


class NameSpace(dict):
    """ Variable names can be added to the namespace with or without an
    initial value.
    
    * If the value is False, its a global/nonlocal, it should not be declared.
    * If the value is True, it should be declared.
    * if the value is a string, it should be declared with the initial value
      specified by the string.
    """
    
    def set_nonlocal(self, key):
        self[key] = False  # also if already exists
    
    def add(self, key):
        if key not in self:
            self[key] = True
    
    def discard(self, key):
        self.pop(key, None)


class Parser0(object):
    """ The Base parser class. Implements the basic mechanism to allow
    parsing to work, but does not implement any parsing on its own.
    
    For details see the Parser class.
    """
    
    # Developer notes:
    # The parse_x() functions are called by parse() with the node of
    # type x. They should return a string or a list of strings. parse()
    # always returns a list of strings.
    
    NAME_MAP = {
        'True'  : 'true',
        'False' : 'false',
        'None'  : 'null',
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
    
    COMP_OP = {
        'Eq'    : "==",
        'NotEq' : "!=",
        'Lt'    : "<",
        'LtE'   : "<=",
        'Gt'    : ">",
        'GtE'   : ">=",
        'Is'    : "===",
        'IsNot' : "!==",
    }
    
    def __init__(self, code, module=None, indent=0, docstrings=True,
                 inline_stdlib=True):
        self._pycode = code  # helpfull during debugging
        self._root = ast.parse(code)
        self._stack = []
        self._indent = indent
        self._dummy_counter = 0
        
        # To keep track of std lib usage
        self._std_functions = set()
        self._std_methods = set()
        self._imported_objects = set()
        self._imports = {}
        
        # To help distinguish classes from functions
        self._seen_func_names = set()
        self._seen_class_names = set()
        
        # Options
        self._docstrings = bool(docstrings)  # whether to inclue docstrings
        
        # Collect function and method handlers
        self._functions, self._methods = {}, {}
        for name in dir(self.__class__):
            if name.startswith('function_'):
                self._functions[name[9:]] = getattr(self, name)
            elif name.startswith('method_'):
                self._methods[name[7:]] = getattr(self, name)
        
        # Prepare
        self.push_stack('module', module or '')
        if module:
            self._indent += 1
        
        # Parse
        try:
            self._parts = self.parse(self._root)
        except JSError as err:
            # Give smarter error message
            _, _, tb = sys.exc_info()
            try:
                msg = self._better_js_error(tb)
            except Exception:  # pragma: no cover
                raise(err)
            else:
                err.args = (msg + ':\n' + str(err), )
                raise(err)
        
        # Finish
        ns = self.pop_stack()  # Pop module namespace
        if ns:
            self._parts.insert(0, self.get_declarations(ns))
        
        # Add part of the stdlib that was actually used
        if inline_stdlib:
            libcode = stdlib.get_partial_std_lib(self._std_functions,
                                                 self._std_methods,
                                                 self._imported_objects,
                                                 self._indent)
            if libcode:
                self._parts.insert(0, libcode)
        
        # Post-process
        if module:
            self._indent -= 1
            exports = [name for name in sorted(ns) if not name.startswith('_')]
            export_keyvals = [repr(name) + ': ' + name for name in exports]
            code = self._parts
            code.insert(0, get_module_preamble(module, []))
            code.append('\n    return {%s};\n' % ', '.join(export_keyvals))
            code.append('}));\n')
            
        else:
            if self._parts:
                self._parts[0] = '    ' * indent + self._parts[0].lstrip()
    
    def dump(self):
        """ Get the JS code as a string.
        """
        return ''.join(self._parts)
    
    def _better_js_error(self, tb):  # pragma: no cover
        """ If we get a JSError, we try to get the corresponding node
        and print the lineno as well as the function etc.
        """
        node = None
        classNode = None
        funcNode = None
        while tb.tb_next:
            tb = tb.tb_next
            node = tb.tb_frame.f_locals.get('node', node)
            classNode = node if isinstance(node, ast.ClassDef) else classNode
            funcNode = node if isinstance(node, ast.FunctionDef) else funcNode
        
        msg = 'Error processing %s-node' % (node.__class__.__name__)
        if classNode:
            msg += ' in class "%s"' % classNode.name
        if funcNode:
            msg += ' in function "%s"' % funcNode.name
        if hasattr(node, 'lineno'):
            msg += ' on line %i' % node.lineno
        if hasattr(node, 'col_offset'):
            msg += ':%i' % node.col_offset
        return msg
    
    def push_stack(self, type, name):
        """ New namespace stack. Match a call to this with a call to
        pop_stack() and process the resulting line to declare the used
        variables. type must be 'module', 'class' or 'function'.
        """
        assert type in ('module', 'class', 'function')
        self._stack.append((type, name, NameSpace()))
    
    def pop_stack(self):
        """ Pop the current stack and return the namespace.
        """
        nstype, nsname, ns = self._stack.pop(-1)
        return ns
    
    def get_declarations(self, ns):
        """ Get string with variable (and buildin-function) declarations.
        """
        if not ns:
            return ''
        code = []
        loose_vars = []
        for name, value in sorted(ns.items()):
            if value and isinstance(value, str):
                code.append(self.lf('var %s = %s;' % (name, value)))
            elif value:
                loose_vars.append(name)
            else:
                pass  # global/nonlocal
        if loose_vars:
            code.insert(0, self.lf('var %s;' % ', '.join(loose_vars)))
        return ''.join(code)
    
    def with_prefix(self, name, new=False):
        """ Add class prefix to a variable name if necessary.
        """
        nstype, nsname, ns = self._stack[-1]
        if nstype == 'class':
            return nsname + '.prototype.' + name
        else:
            return name
    
    @property
    def vars(self):
        """ NameSpace instance for the current stack. """
        return self._stack[-1][2]
    
    def lf(self, code=''):
        """ Line feed - create a new line with the correct indentation.
        """
        return '\n' + self._indent * '    ' + code
    
    def dummy(self, name=''):
        """ Get a unique name. The name is added to vars.
        """
        self._dummy_counter += 1
        name = 'dummy%i_%s' % (self._dummy_counter, name)
        self.vars.add(name)
        return name
    
    def use_std_function(self, name, arg_nodes):
        """ Use a function from the PyScript standard library.
        """
        self._std_functions.add(name)
        mangled_name = stdlib.FUNCTION_PREFIX + name
        args = [(a if isinstance(a, str) else unify(self.parse(a)))
                for a in arg_nodes]
        return '%s(%s)' % (mangled_name, ', '.join(args))
    
    def use_std_method(self, base, name, arg_nodes):
        """ Use a method from the PyScript standard library.
        """
        self._std_methods.add(name)
        mangled_name = stdlib.METHOD_PREFIX + name
        args = [(a if isinstance(a, str) else unify(self.parse(a)))
                for a in arg_nodes]
        return '%s.%s(%s)' % (base, mangled_name, ', '.join(args)) 
    
    def use_imported_object(self, name):
        self._imported_objects.add(name)
        return stdlib.IMPORT_PREFIX + name.replace('.', stdlib.IMPORT_DOT)
        
    def pop_docstring(self, node):
        """ If a docstring is present, in the body of the given node,
        remove that string node and return it as a string, corrected
        for indentation and stripped. If no docstring is present return
        empty string.
        """
        docstring = ''
        if (node.body_nodes and isinstance(node.body_nodes[0], ast.Expr) and
                                isinstance(node.body_nodes[0].value_node, ast.Str)):
            docstring = node.body_nodes.pop(0).value_node.value.strip()
            lines = docstring.splitlines()
            getindent = lambda x: len(x) - len(x.strip())
            indent = min([getindent(x) for x in lines[1:]]) if (len(lines) > 1) else 0
            if lines:
                lines[0] = ' ' * indent + lines[0]
                lines = [line[indent:] for line in lines]
            docstring = '\n'.join(lines)
        return docstring
    
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
