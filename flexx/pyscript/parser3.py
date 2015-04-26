"""

Pythonic sugar
--------------

Several common buildin functions are automatically translated to
JavaScript.

.. pyscript_example::

    # "self" is replaced with "this"
    self.foo
    
    # Printing just works
    print('some test')
    print(a, b, c, sep='-')
    
    # Getting the length of a string or array
    len(foo)
    
    # Rounding
    round(foo)  # round to nearest integer
    int(foo)  # round towards 0 as in Python
    
    # min and max
    min(foo)
    min(a, b, c)
    max(foo)
    max(a, b, c)
    
    # Summing elements
    sum(foo)


The isinstance function
-----------------------

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
    
    a = {'foo', 3}
    a['foo']
    a.get('foo', 0)
    a.get('foo')
    a.keys()

"""

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


class Parser3(Parser2):
    """ Parser to transcompile Python to JS, allowing more Pythonic
    code, like ``self``, ``print()``, ``len()``, list methods, etc.
    """
    
    NAME_MAP = {'self': 'this', }
    NAME_MAP.update(Parser2.NAME_MAP)
    
    ## Functions
    
    def function_isinstance(self, node):
        if len(node.args) != 2:
            raise JSError('isinstance expects two arguments.')
        
        ob = unify(self.parse(node.args[0]))
        cls = unify(self.parse(node.args[1]))
        if cls[0] in '"\'':
            cls = cls[1:-1]  # remove quotes
        
        BASIC_TYPES = ('number', 'boolean', 'string', 'function', 'array',
                       'object', 'null', 'undefined')
        
        MAP = {'(int, float)': 'number', '(float, int)': 'number', 'float': 'number',
               'str': 'string', 'basestring': 'string', 'string_types': 'string',
               'bool': 'boolean',
               'FunctionType': 'function', 'types.FunctionType': 'function',
               'list': 'array', 'tuple': 'array',
               '(list, tuple)': 'array', '(tuple, list)': 'array',
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
    
    def function_print(self, node):
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
    
    def function_len(self, node):
        if len(node.args) == 1:
            return unify(self.parse(node.args[0])), '.length'
        else:
            return None  # don't apply this feature
    
    def function_sum(self, node):
        if len(node.args) == 1:
            return (unify(self.parse(node.args[0])),
                    '.reduce(function(a, b) {return a + b;})')
        else:
            raise JSError('sum() needs exactly one argument')
    
    def function_round(self, node):
        if len(node.args) == 1:
            arg = ''.join(self.parse(node.args[0]))
            return 'Math.round(', arg, ')'
        else:
            raise JSError('round() needs at least one argument')
    
    def function_int(self, node):
        if len(node.args) == 1:
            arg = ''.join(self.parse(node.args[0]))
            return '(%s<0? Math.ceil(%s): Math.floor(%s))' % (arg, arg, arg)
        else:
            raise JSError('int() needs at least one argument')
    
    def function_max(self, node):
        if len(node.args) == 0:
            raise JSError('max() needs at least one argument')
        elif len(node.args) == 1:
            arg = ''.join(self.parse(node.args[0]))
            return 'Math.max.apply(null, ', arg, ')'
        else:
            args = ', '.join([unify(self.parse(arg)) for arg in node.args])
            return 'Math.max(', args, ')'
    
    def function_min(self, node):
        if len(node.args) == 0:
            raise JSError('min() needs at least one argument')
        elif len(node.args) == 1:
            arg = ''.join(self.parse(node.args[0]))
            return 'Math.min.apply(null, ', arg, ')'
        else:
            args = ', '.join([unify(self.parse(arg)) for arg in node.args])
            return 'Math.min(', args, ')'
    
    ## List methods
    
    def method_append(self, node, base):
        if len(node.args) == 1:
            code = []
            code.append('(%s.append || %s.push).apply(%s, [' % (base, base, base))
            code += self.parse(node.args[0])
            code.append('])')
            return code
    
    def method_remove(self, node, base):
        if len(node.args) == 1:
            code = []
            remove_func = 'function (x) {this.splice(this.indexOf(x), 1);}'
            code.append('(%s.remove || %s).apply(%s, [' % (base, remove_func, base))
            code += self.parse(node.args[0])
            code.append('])')
            return code
    
    ## Dict methods
    
    def method_get(self, node, base):
        if len(node.args) in (1, 2):
            key = unify(self.parse(node.args[0]))
            default = 'null'
            if len(node.args) == 2:
                default = unify(self.parse(node.args[1]))
            return '(%s[%s] || %s)' % (base, key, default)
    
    def method_keys(self, node, base):
        if len(node.args) == 0:
            return 'Object.keys(%s)' % base
