"""

Python Builtins
---------------

Most buildin functions (that make sense in JS) are automatically
translated to JavaScript: isinstance, issubclass, callable, hasattr,
getattr, setattr, delattr, print, len, max, min, chr, ord, dict, list,
tuple, range, pow, sum, round, int, float, str, bool, abs, divmod, all,
any, enumerate, zip, reversed, sorted, filter, map.

Further all methods for list, dict and str are implemented (except str
methods: encode, decode, format, format_map, isdecimal, isdigit,
isprintable, maketrans).

.. pyscript_example::

    # "self" is replaced with "this"
    self.foo
    
    # Printing just works
    print('some test')
    print(a, b, c, sep='-')
    
    # Getting the length of a string or array
    len(foo)
    
    # Rounding and abs
    round(foo)  # round to nearest integer
    int(foo)  # round towards 0 as in Python
    abs(foo)
    
    # min and max
    min(foo)
    min(a, b, c)
    max(foo)
    max(a, b, c)
    
    # divmod
    a, b = divmod(100, 7)  # -> 14, 2
    
    # Aggregation
    sum(foo)
    all(foo)
    any(foo)
    
    # Turning things into numbers, bools and strings
    str(s)
    float(x)
    bool(y)
    int(z)  # this rounds towards zero like in Python
    chr(65)  # -> 'A'
    ord('A')  # -> 65
    
    # Turning things into lists and dicts
    dict([['foo', 1], ['bar', 2]])  # -> {'foo': 1, 'bar': 2}
    list('abc')  # -> ['a', 'b', 'c']
    dict(other_dict)  # make a copy
    list(other_list)  # make copy


The isinstance function (and friends)
-------------------------------------

The ``isinstance()`` function works for all JS primitive types, but also
for user-defined classes.

.. pyscript_example::

    # Basic types
    isinstance(3, float)  # in JS there are no ints
    isinstance('', str)
    isinstance([], list)
    isinstance({}, dict)
    isinstance(foo, types.FunctionType)
    
    # Can also use JS strings
    isinstance(3, 'number')
    isinstance('', 'string')
    isinstance([], 'array')
    isinstance({}, 'object')
    isinstance(foo, 'function')
    
    # You can use it on your own types too ...
    isinstance(x, MyClass)
    isinstance(x, 'MyClass')  # equivalent
    isinstance(x, 'Object')  # also yields true (subclass of Object)
    
    # issubclass works too
    issubclass(Foo, Bar)
    
    # As well as callable
    callable(foo)


hasattr, getattr, setattr and delattr
-------------------------------------

.. pyscript_example::
    
    a = {'foo': 1, 'bar': 2}
    
    hasattr(a, 'foo')  # -> True
    hasattr(a, 'fooo')  # -> False
    hasattr(null, 'foo')  # -> False
    
    getattr(a, 'foo')  # -> 1
    getattr(a, 'fooo')  # -> raise AttributeError
    getattr(a, 'fooo', 3)  # -> 3
    getattr(null, 'foo', 3)  # -> 3
    
    setattr(a, 'foo', 2)
    
    delattr(a, 'foo')


Creating sequences
------------------

.. pyscript_example::
    
    range(10)
    range(2, 10, 2)
    range(100, 0, -1)
    
    reversed(foo)
    sorted(foo)
    enumerate(foo)
    zip(foo, bar)
    
    filter(func, foo)
    map(func, foo)


List methods
------------

.. pyscript_example::

    # Call a.append() if it exists, otherwise a.push()
    a.append(x)
    
    # Similar for remove()
    a.remove(x)


Dict methods
------------

.. pyscript_example::
    
    a = {'foo': 3}
    a['foo']
    a.get('foo', 0)
    a.get('foo')
    a.keys()


Str methods
-----------

.. pyscript_example::

    "foobar".startswith('foo')
    "foobar".replace('foo', 'bar')
    "foobar".upper()


Using JS specific functionality
-------------------------------

When writing PyScript inside Python modules, we recommend that where
specific JavaScript functionality is used, that the references are
prefixed with ``window.`` Where ``window`` represents the global JS 
namespace. All global JavaScript objects, functions, and variables
automatically become members of the ``window`` object. This helps
make it clear that the functionality is specific to JS, and also
helps static code analysis tools like flake8.

.. pyscript_example::
    
    from flexx.pyscript import window  # this is a stub
    def foo(a):
        return window.Math.cos(a)

Aside from ``window``, ``flexx.pyscript`` also provides ``undefined``,
``Inifinity``, and ``NaN``.

"""

from . import commonast as ast
from . import stdlib
from .parser2 import Parser2, JSError, unify  # noqa
from .stubs import RawJS


# This class has several `function_foo()` and `method_bar()` methods
# to implement corresponding functionality. Most of these are
# auto-generated from the stdlib. However, some methods need explicit
# implementation, e.g. to parse keyword arguments, or are inlined rather
# than implemented via the stlib.
#
# Note that when the number of arguments does not match, almost all
# functions raise a compile-time error. The methods, however, will
# bypass the stdlib in this case, because it is assumed that the user
# intended to call a special method on the object.


class Parser3(Parser2):
    """ Parser to transcompile Python to JS, allowing more Pythonic
    code, like ``self``, ``print()``, ``len()``, list methods, etc.
    """
    
    def function_this_is_js(self, node):
        # Note that we handle this_is_js() shortcuts in the if-statement
        # directly. This replacement with a string is when this_is_js()
        # is used outside an if statement.
        if len(node.arg_nodes) != 0:
            raise JSError('this_is_js() expects zero arguments.')
        return ('"this_is_js()"')
    
    def function_RawJS(self, node):
        if len(node.arg_nodes) == 1:
            if not isinstance(node.arg_nodes[0], ast.Str):
                raise JSError('RawJS needs a verbatim string (use multiple '
                              'args to bypass PyScript\'s RawJS).')
            lines = RawJS._str2lines(node.arg_nodes[0].value)
            indent = (self._indent * 4) * ' '
            return '\n'.join([indent + line for line in lines])
        else:
            return None  # maybe RawJS is a thing
    
    ## Python buildin functions
    
    
    def function_isinstance(self, node):
        if len(node.arg_nodes) != 2:
            raise JSError('isinstance() expects two arguments.')
        
        ob = unify(self.parse(node.arg_nodes[0]))
        cls = unify(self.parse(node.arg_nodes[1]))
        if cls[0] in '"\'':
            cls = cls[1:-1]  # remove quotes
        
        BASIC_TYPES = ('number', 'boolean', 'string', 'function', 'array',
                       'object', 'null', 'undefined')
        
        MAP = {'[int, float]': 'number', '[float, int]': 'number', 'float': 'number',
               'str': 'string', 'basestring': 'string', 'string_types': 'string',
               'bool': 'boolean',
               'FunctionType': 'function', 'types.FunctionType': 'function',
               'list': 'array', 'tuple': 'array',
               '[list, tuple]': 'array', '[tuple, list]': 'array',
               'dict': 'object',
        }
        
        cmp = MAP.get(cls, cls)
        
        if cmp.lower() in BASIC_TYPES:
            # Basic type, use Object.prototype.toString
            # http://stackoverflow.com/questions/11108877
            return ["({}).toString.call(",
                    ob,
                    ").match(/\s([a-zA-Z]+)/)[1].toLowerCase() === ",
                    "'%s'" % cmp.lower()
                    ]
        
        else:
            # User defined type, use instanceof
            # http://tobyho.com/2011/01/28/checking-types-in-javascript/
            cmp = unify(cls)
            if cmp[0] == '(':
                raise JSError('isinstance() can only compare to simple types')
            return ob, " instanceof ", cmp
    
    def function_issubclass(self, node):
        # issubclass only needs to work on custom classes
        if len(node.arg_nodes) != 2:
            raise JSError('issubclass() expects two arguments.')
        
        cls1 = unify(self.parse(node.arg_nodes[0]))
        cls2 = unify(self.parse(node.arg_nodes[1]))
        if cls2 == 'object':
            cls2 = 'Object'
        return '(%s.prototype instanceof %s)' % (cls1, cls2)
    
    def function_print(self, node):
        # Process keywords
        sep, end = '" "', ''
        for kw in node.kwarg_nodes:
            if kw.name == 'sep':
                sep = ''.join(self.parse(kw.value_node))
            elif kw.name == 'end':
                end = ''.join(self.parse(kw.value_node))
            elif kw.name in ('file', 'flush'):
                raise JSError('print() file and flush args not supported')
            else:
                raise JSError('Invalid argument for print(): %r' % kw.name)
        
        # Combine args
        args = [unify(self.parse(arg)) for arg in node.arg_nodes]
        end = (" + %s" % end) if (args and end and end != '\n') else ''
        combiner = ' + %s + ' % sep
        args_concat = combiner.join(args) or '""'
        return 'console.log(' + args_concat + end + ')'
    
    def function_len(self, node):
        if len(node.arg_nodes) == 1:
            return unify(self.parse(node.arg_nodes[0])), '.length'
        else:
            return None  # don't apply this feature
    
    def function_max(self, node):
        if len(node.arg_nodes) == 0:
            raise JSError('max() needs at least one argument')
        elif len(node.arg_nodes) == 1:
            arg = ''.join(self.parse(node.arg_nodes[0]))
            return 'Math.max.apply(null, ', arg, ')'
        else:
            args = ', '.join([unify(self.parse(arg)) for arg in node.arg_nodes])
            return 'Math.max(', args, ')'
    
    def function_min(self, node):
        if len(node.arg_nodes) == 0:
            raise JSError('min() needs at least one argument')
        elif len(node.arg_nodes) == 1:
            arg = ''.join(self.parse(node.arg_nodes[0]))
            return 'Math.min.apply(null, ', arg, ')'
        else:
            args = ', '.join([unify(self.parse(arg)) for arg in node.arg_nodes])
            return 'Math.min(', args, ')'
    
    def function_callable(self, node):
        if len(node.arg_nodes) == 1:
            arg = unify(self.parse(node.arg_nodes[0]))
            return '(typeof %s === "function")' % arg
        else:
            raise JSError('callable() needs at least one argument')
    
    def function_chr(self, node):
        if len(node.arg_nodes) == 1:
            arg = ''.join(self.parse(node.arg_nodes[0]))
            return 'String.fromCharCode(%s)' % arg
        else:
            raise JSError('chr() needs at least one argument')
    
    def function_ord(self, node):
        if len(node.arg_nodes) == 1:
            arg = ''.join(self.parse(node.arg_nodes[0]))
            return '%s.charCodeAt(0)' % arg
        else:
            raise JSError('ord() needs at least one argument')
    
    def function_dict(self, node):
        if len(node.arg_nodes) == 0:
            kwargs = ['%s:%s' % (arg.name, unify(self.parse(arg.value_node)))
                      for arg in node.kwarg_nodes]
            return '{%s}' % ', '.join(kwargs)
        if len(node.arg_nodes) == 1:
            return self.use_std_function('dict', node.arg_nodes)
        else:
            raise JSError('dict() needs at least one argument')
    
    def function_list(self, node):
        if len(node.arg_nodes) == 0:
            return '[]'
        if len(node.arg_nodes) == 1:
            return self.use_std_function('list', node.arg_nodes)
        else:
            raise JSError('list() needs at least one argument')
    
    def function_tuple(self, node):
        return self.function_list(node)
    
    def function_range(self, node):
        if len(node.arg_nodes) == 1:
            args = ast.Num(0), node.arg_nodes[0], ast.Num(1)
            return self.use_std_function('range', args)
        elif len(node.arg_nodes) == 2:
            args = node.arg_nodes[0], node.arg_nodes[1], ast.Num(1)
            return self.use_std_function('range', args)
        elif len(node.arg_nodes) == 3:
            return self.use_std_function('range', node.arg_nodes)
        else:
            raise JSError('range() needs 1, 2 or 3 arguments')
    
    def function_sorted(self, node):
        if len(node.arg_nodes) == 1:
            key, reverse = ast.Name('undefined'), ast.NameConstant(False)
            for kw in node.kwarg_nodes:
                if kw.name == 'key':
                    key = kw.value_node
                elif kw.name == 'reverse':
                    reverse = kw.value_node
                else:
                    raise JSError('Invalid keyword argument for sorted: %r' % kw.name)
            return self.use_std_function('sorted', [node.arg_nodes[0], key, reverse])
        else:
            raise JSError('sorted() needs one argument')
    
    ## Methods of list/dict/str
    
    def method_sort(self, node, base):
        if len(node.arg_nodes) == 0:  # sorts args are keyword-only
            key, reverse = ast.Name('undefined'), ast.NameConstant(False)
            for kw in node.kwarg_nodes:
                if kw.name == 'key':
                    key = kw.value_node
                elif kw.name == 'reverse':
                    reverse = kw.value_node
                else:
                    raise JSError('Invalid keyword argument for sort: %r' % kw.name)
            return self.use_std_method(base, 'sort', [key, reverse])


# Add functions and methods to the class, using the stdib functions ...

def make_function(name, nargs, function_deps, method_deps):
    def function_X(self, node):
        if node.kwarg_nodes:
            raise JSError('Function %s does not support keyword args.' % name)
        if len(node.arg_nodes) not in nargs:
            raise JSError('Function %s needs #args in %r.' % (name, nargs))
        for dep in function_deps:
            self.use_std_function(dep, [])
        for dep in method_deps:
            self.use_std_method('x', dep, [])
        return self.use_std_function(name, node.arg_nodes)
    return function_X

def make_method(name, nargs, function_deps, method_deps):
    def method_X(self, node, base):
        if node.kwarg_nodes:
            raise JSError('Method %s does not support keyword args.' % name)
        if len(node.arg_nodes) not in nargs:
            return None  # call as-is, don't use our variant
        for dep in function_deps:
            self.use_std_function(dep, [])
        for dep in method_deps:
            self.use_std_method('x', dep, [])
        return self.use_std_method(base, name, node.arg_nodes)
    return method_X

for name, code in stdlib.METHODS.items():
    nargs, function_deps, method_deps = stdlib.get_std_info(code)
    if nargs and not hasattr(Parser3, 'method_' + name):
        m = make_method(name, tuple(nargs), function_deps, method_deps)
        setattr(Parser3, 'method_' + name, m)

for name, code in stdlib.FUNCTIONS.items():
    nargs, function_deps, method_deps = stdlib.get_std_info(code)
    if nargs and not hasattr(Parser3, 'function_' + name):
        m = make_function(name, tuple(nargs), function_deps, method_deps)
        setattr(Parser3, 'function_' + name, m)
