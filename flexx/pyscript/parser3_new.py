"""

Python Builtins
---------------

Most buildin functions (that make sense in JS) are automatically
translated to JavaScript: isinstance, issubclass, callable, hasattr,
getattr, setattr, delattr, print, len, max, min, chr, ord, dict, list,
tuple, range, pow, sum, round, int, float, str, bool, abs, divmod, all,
any, enumerate, zip, reversed, sorted, filter, map.

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


Additional sugar
----------------

.. pyscript_example::
    
    # Get time (number of seconds since epoch)
    print(time.time())
    
    # High resolution timer (as in time.perf_counter on Python 3)
    t0 = time.perf_counter()
    do_something()
    t1 = time.perf_counter()
    print('this took me', t1-t0, 'seconds')

"""

from . import commonast as ast
from .parser2 import Parser2, JSError, unify  # noqa

# List of possibly relevant builtin functions:
#
# abs all any bin bool callable chr complex delattr dict dir divmod
# enumerate eval exec filter float format getattr globals hasattr hash
# hex id int isinstance issubclass iter len list locals map max min next
# object oct ord pow print property range repr reversed round set setattr
# slice sorted str sum super tuple type vars zip
#
# Further, all methods of: list, dict, str, set?

# todo: make these more robust 
# by not applying the Python version if a JS version exists.

class Parser3(Parser2):
    """ Parser to transcompile Python to JS, allowing more Pythonic
    code, like ``self``, ``print()``, ``len()``, list methods, etc.
    """
    
    NAME_MAP = {'self': 'this', }
    NAME_MAP.update(Parser2.NAME_MAP)
    
    ## Hardcore functions (hide JS functions with the same name)
    
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
                    repr(cmp.lower())
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
    
    def function_hasattr(self, node):
        if len(node.arg_nodes) == 2:
            return self.use_std_func('hasattr', node.arg_nodes)
        else:
            raise JSError('hasattr() expects two arguments.')
    
    def function_getattr(self, node):
        if len(node.arg_nodes) in (2, 3):
            return self.use_std_func('getattr', node.arg_nodes)
        else:
            raise JSError('hasattr() expects two or three arguments.')
    
    def function_setattr(self, node):
        if len(node.arg_nodes) == 3:
            return self.use_std_func('setattr', node.arg_nodes)
        else:
            raise JSError('setattr() expects three arguments.')
    
    def function_delattr(self, node):
        if len(node.arg_nodes) == 2:
            return self.use_std_func('delattr', node.arg_nodes)
        else:
            raise JSError('delattr() expects two arguments.')
    
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
        args_concat = combiner.join(args)
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
            return '{}'
        if len(node.arg_nodes) == 1:
            return self.use_std_func('dict', node.arg_nodes)
        else:
            raise JSError('dict() needs at least one argument')
    
    def function_list(self, node):
        if len(node.arg_nodes) == 0:
            return '[]'
        if len(node.arg_nodes) == 1:
            return self.use_std_func('list', node.arg_nodes)
        else:
            raise JSError('list() needs at least one argument')
    
    def function_tuple(self, node):
        return self.function_list(node)
    
    def function_range(self, node):
        fun = ('function (start, end, step) {var i, res = []; '
                'for (i=start; i<end; i+=step) {res.push(i);} return res;}')
        
        if len(node.arg_nodes) == 1:
            args = ast.Num(0), node.arg_nodes[0], ast.Num(1)
            return self.use_std_func('range', args)
        elif len(node.arg_nodes) == 2:
            args = node.arg_nodes[0], node.arg_nodes[1], ast.Num(1)
            return self.use_std_func('range', args)
        elif len(node.arg_nodes) == 3:
            return self.use_std_func('range', node.arg_nodes)
        else:
            raise JSError('range() needs 1, 2 or 3 arguments')
    
    ## Normal functions
    
    def function_pow(self, node):
        if len(node.arg_nodes) == 2:
            return self.use_std_func('pow', node.arg_nodes)
        else:
            raise JSError('pow() needs exactly two argument2')
    
    def function_sum(self, node):
        if len(node.arg_nodes) == 1:
            return self.use_std_func('sum', node.arg_nodes)
            # code = 'function (x) {return x.reduce(function(a, b) {return a + b;});}'
            # self.vars_for_functions['sum'] = code
            # return None
        else:
            raise JSError('sum() needs exactly one argument')
    
    def function_round(self, node):
        if len(node.arg_nodes) == 1:
            return self.use_std_func('round', node.arg_nodes)
        else:
            raise JSError('round() needs at least one argument')
    
    def function_int(self, node):
        # No need to turn into number first
        if len(node.arg_nodes) == 1:
            return self.use_std_func('int', node.arg_nodes)
            # code = 'function (x) {return x<0 ? Math.ceil(x): Math.floor(x);}'
            # self.vars_for_functions['int'] = code
        else:
            raise JSError('int() needs one argument')
    
    def function_float(self, node):
        if len(node.arg_nodes) == 1:
            return self.use_std_func('float', node.arg_nodes)
            # self.vars_for_functions['float'] = 'Number'
        else:
            raise JSError('float() needs one argument')
    
    def function_str(self, node):
        if len(node.arg_nodes) in (0, 1):
            return self.use_std_func('str', node.arg_nodes)
            # self.vars_for_functions['str'] = 'String'
        else:
            raise JSError('str() needs zero or one argument')
    
    def function_repr(self, node):
        if len(node.arg_nodes) == 1:
            return self.use_std_func('repr', node.arg_nodes)
            # self.vars_for_functions['repr'] = 'JSON.stringify'
        else:
            raise JSError('repr() needs one argument')
    
    def function_bool(self, node):
        if len(node.arg_nodes) == 1:
            self.use_std_func('truthy', [])  # trigger truthy usage
            return self.use_std_func('bool', node.arg_nodes)
            # self._wrap_truthy(ast.Name('x'))  # trigger _truthy function declaration
            # self.vars_for_functions['bool'] = ('function (x) {'
            #                                    'return Boolean(_truthy(x));}')
        else:
            raise JSError('bool() needs one argument')
    
    def function_abs(self, node):
        if len(node.arg_nodes) == 1:
            return self.use_std_func('abs', node.arg_nodes)
            # self.vars_for_functions['abs'] = 'Math.abs'
        else:
            raise JSError('abs() needs one argument')
    
    def function_divmod(self, node):
        if len(node.arg_nodes) == 2:
            return self.use_std_func('divmod', node.arg_nodes)
            # code = 'function (x, y) {var m = x % y; return [(x-m)/y, m];}'
            # self.vars_for_functions['divmod'] = code
        else:
            raise JSError('divmod() needs two arguments')
        
    def function_all(self, node):
        if len(node.arg_nodes) == 1:
            self.use_std_func('truthy', [])  # trigger truthy usage
            return self.use_std_func('all', node.arg_nodes)
            # self._wrap_truthy(ast.Name('x'))  # trigger _truthy function declaration
            # code = ('function (x) {for (var i=0; i<x.length; i++) {'
            #         'if (!_truthy(x[i])){return false}} return true;}')
            # self.vars_for_functions['all'] = code
        else:
            raise JSError('all() needs one argument')
    
    def function_any(self, node):
        if len(node.arg_nodes) == 1:
            self.use_std_func('truthy', [])  # trigger truthy usage
            return self.use_std_func('any', node.arg_nodes)
            # self._wrap_truthy(ast.Name('x'))  # trigger _truthy function declaration
            # code = ('function (x) {for (var i=0; i<x.length; i++) {'
            #         'if (_truthy(x[i])){return true}} return false;}')
            # self.vars_for_functions['any'] = code
        else:
            raise JSError('any() needs one argument')
    
    def function_enumerate(self, node):
        if len(node.arg_nodes) == 1:
            return self.use_std_func('enumerate', node.arg_nodes)
            # code = 'function (iter) { var i, res=[];'
            # code += self._make_iterable('iter', 'iter', False)
            # code += 'for (i=0; i<iter.length; i++) {res.push([i, iter[i]]);}'
            # code += 'return res;}'
            # self.vars_for_functions['enumerate'] = code
        else:
            raise JSError('enumerate() needs one argument')
    
    def function_zip(self, node):
        if len(node.arg_nodes) == 2:
            return self.use_std_func('zip', node.arg_nodes)
            # code = 'function (iter1, iter2) { var i, res=[];'
            # code += self._make_iterable('iter1', 'iter1', False)
            # code += self._make_iterable('iter2', 'iter2', False)
            # code += 'var len = Math.min(iter1.length, iter2.length);'
            # code += 'for (i=0; i<len; i++) {res.push([iter1[i], iter2[i]]);}'
            # code += 'return res;}'
            # self.vars_for_functions['zip'] = code
        else:
            raise JSError('zip() needs two arguments')
             
    def function_reversed(self, node):
        if len(node.arg_nodes) == 1:
            return self.use_std_func('reversed', node.arg_nodes)
            # code = 'function (iter) {'
            # code += self._make_iterable('iter', 'iter', False)
            # code += 'return iter.slice().reverse();}'
            # self.vars_for_functions['reversed'] = code
        else:
            raise JSError('reversed() needs one argument')
    
    def function_sorted(self, node):
        if len(node.arg_nodes) == 1:
            return self.use_std_func('sorted', node.arg_nodes)
            # code = 'function (iter) {'
            # code += self._make_iterable('iter', 'iter', False)
            # code += 'return iter.slice().sort();}'
            # self.vars_for_functions['sorted'] = code
        else:
            raise JSError('sorted() needs one argument')
    
    def function_filter(self, node):
        if len(node.arg_nodes) == 2:
            return self.use_std_func('filter', node.arg_nodes)
            # code = 'function (func, iter) {'
            # code += ('if (typeof func === "undefined" || func === null) '
            #          '{func = function(x) {return x;}}')
            # code += 'return iter.filter(func);}'
            # self.vars_for_functions['filter'] = code
        else:
            raise JSError('filter() needs two arguments')
    
    def function_map(self, node):
        if len(node.arg_nodes) == 2:
            return self.use_std_func('map', node.arg_nodes)
            # code = 'function (func, iter) {return iter.map(func);}'
            # self.vars_for_functions['map'] = code
        else:
            raise JSError('map() needs two arguments')
    
    ## List methods
    
    def method_append(self, node, base):
        if len(node.arg_nodes) == 1:
            return self.use_std_method(base, 'append', node.arg_nodes)
    
    def method_remove(self, node, base):
        if len(node.arg_nodes) == 1:
            return self.use_std_method(base, 'remove', node.arg_nodes)
    
    ## Dict methods
    
    def method_get(self, node, base):
        if len(node.arg_nodes) in (1, 2):
            return self.use_std_method(base, 'get', node.arg_nodes)
    
    def method_keys(self, node, base):
        if len(node.arg_nodes) == 0:
            return 'Object.keys(%s)' % base
    
    ## Str methods
    
    def method_startswith(self, node, base):
        if len(node.arg_nodes) == 1:
            arg = unify(self.parse(node.arg_nodes[0]))
            return unify(base), '.indexOf(', arg, ') == 0'
    
    ## Extra functions / methods
    
    def method_time(self, node, base):  # time.time()
        if base == 'time':
            if len(node.arg_nodes) == 0:
                return '((new Date()).getTime() / 1000)'
            else:
                raise JSError('time() needs no argument')
    
    def method_perf_counter(self, node, base):  # time.perf_counter()
        if base == 'time':
            if len(node.arg_nodes) == 0:
                # Work in nodejs and browser
                dummy = self.dummy()
                return ('(typeof(process) === "undefined" ? performance.now()*1e-3 '
                        ': ((%s=process.hrtime())[0] + %s[1]*1e-9))' % (dummy, dummy))
            else:
                raise JSError('perf_counter() needs no argument')
