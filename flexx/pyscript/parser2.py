"""

If statements
-------------


.. pyscript_example::

    if val > 7:
        result = 42
    elif val > 1:
        result = 1
    else:
        result = 0
    
    # One-line if
    result = 42 if truth else 0
    
    
Looping
-------

There is support for while loops and for-loops in several forms.
Both support ``continue``, ``break`` and the ``else`` clause.

.. pyscript_example::

    # While loops map well to JS
    val = 0
    while val < 10:
        val += 1
    
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
    
    # Which is why we recommend using keys(), values(), or items()
    for key in d.keys():
        print(key)
    
    for val in d.values():
        print(val)
    
    for key, val in d.items():
        print(key, val, sep=': ')
    
    
Defining functions
------------------

.. pyscript_example::

    def display(val):
        print(val)
    
    # Support for *args
    def foo(x, *values):
        bar(x+1, *values)
    
    # To write raw JS, define a function with only a docstring
    def bar(a, b):
        '''
        var c = 4;
        return a + b + c;
        '''
    
    # Lambda expressions
    foo = lambda x: x**2


Defining classes
----------------

Classes are translated to the JavaScript prototypal class paragigm,
which means that they should play well with other JS libraries and e.g.
`instanceof`. Inheritance is supported, but not multiple inheritance.
Further, `super()` works just as in Python 3.

.. pyscript_example::
    
    class Foo:
        a_class_attribute = 4
        def __init__(self):
            self.x = 3
    
    class Bar(Foo):
        def __init__(self):
            super.__init__()
            self.x += 1


Exceptions
----------

Raised exceptions are translated to a JavaScript Error objects, for
which the ``name`` attribute is set to the type of the exception being
raised. When catching exceptions the name attribute is checked (if its
an Error object. You can raise strings or any other kind of object, but
you can only catch Error objects.

.. pyscript_example::
    
    # Throwing/raising exceptions
    raise SomeError('asd')
    raise AnotherError()
    raise "In JS you can throw anything"
    raise 4
    
    # Assertions work too
    assert foo == 3
    assert bar == 4, "bar should be 4"
    
    # Catching exceptions
    try:
        raise IndexError('blabla')
    except IndexError as err:
        print(err)
    except Exception:
       print('something went wrong')

"""

import ast
import sys

from .parser1 import Parser1, JSError, unify  # noqa

# todo: tuple unpacking in for-loops (for x, y, z in xxyyzz)

class Parser2(Parser1):
    """ Parser that adds control flow, functions, classes, and exceptions.
    """
    
    ## Exceptions
    
    def parse_Raise(self, node):
        # We raise the exception as an Error object
        
        if sys.version_info >= (3, ):
            if node.exc is None:
                raise JSError('When raising, provide an error object.')
            if node.cause is not None:
                raise JSError('When raising, "cause" is not supported.')
            err_node = node.exc
        else:  # pragma: no cover
            if node.type is None:
                raise JSError('When raising, provide a type.')
            if node.inst is not None:
                raise JSError('When raising, "instance" is not supported.')
            if node.tback is not None:
                raise JSError('When raising, "tback" is not supported.')
            err_node = node.exc
        
        # Get cls and msg
        err_cls, err_msg = None, "''"
        if isinstance(err_node, ast.Name):
            err_cls = err_node.id
        elif isinstance(err_node, ast.Call):
            err_cls = err_node.func.id
            err_msg = ''.join([unify(self.parse(arg)) for arg in err_node.args])
        else:
            err_msg = ''.join(self.parse(err_node))
        
        err_name = 'err_%i' % self._indent
        self.vars.add(err_name)
        
        # Build code to throw
        code = []
        if err_cls:
            code.append(self.lf("%s = " % err_name))
            code.append('new Error(')
            code.append(repr(err_cls + ':') + ' + ')
        else:
            code.append(self.lf("throw "))
        code.append(err_msg or '""')
        if err_cls:
            code.append(');')
            code.append(' %s.name = "%s";' % (err_name, err_cls))
            code.append(' throw %s;' % err_name)
        else:
            code.append(';')
        
        return code
    
    def parse_Assert(self, node):
        
        test = ''.join(self.parse(node.test))
        msg = test
        if node.msg:
            msg = ''.join(self.parse(node.msg))
        
        code = []
        code.append(self.lf('if (!('))
        code += test
        code.append(')) {')
        code.append('throw "AssertionError: ')  # don't bother with new Error
        code.append(msg)
        code.append('";}')
        return code
    
    def parse_Try(self, node):
        # Python >= 3.3
        if node.finalbody:
            raise JSError('No support for try-finally clause.')
        
        return self.parse_TryExcept(node)
    
    def parse_TryFinally(self, node):
        # Python < 3.3
        raise JSError('No support for try-finally clause.')
    
    def parse_TryExcept(self, node):
        # Python < 3.3
        if node.orelse:
            raise JSError('No support for try-else clause.')
        
        code = []
        
        # Try
        code.append(self.lf('try {'))
        self._indent += 1
        for n in node.body:
            code += self.parse(n)
        self._indent -= 1
        code.append(self.lf('}'))
        
        # Except
        self._indent += 1
        err_name = 'err_%i' % self._indent
        code.append(' catch(%s) {' % err_name)
        for i, handler in enumerate(node.handlers):
            if i == 0:
                code.append(self.lf(''))
            else:
                code.append(' else ')
            code += self.parse(handler)
        
        self._indent -= 1
        code.append(self.lf('}'))  # end catch
        
        return code
        
    def parse_ExceptHandler(self, node):
        err_name = 'err_%i' % self._indent
        
        # Setup the catch
        code = []
        err_type = unify(self.parse(node.type)) if node.type else ''
        if err_type and err_type != 'Exception':
            code.append('if (%s instanceof Error && %s.name === "%s") {' %
                        (err_name, err_name, err_type))
        else:
            code.append('{')
        self._indent += 1
        if node.name:
            code.append(self.lf('%s = %s;' % (node.name, err_name)))
            self.vars.add(node.name)
        
        # Insert the body
        for n in node.body:
            code += self.parse(n)
        self._indent -= 1
        
        code.append(self.lf('}'))
        return code
    
    ## Control flow
    
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
    
    def parse_If(self, node):
        if (True and isinstance(node.test, ast.Compare) and
                     isinstance(node.test.left, ast.Name) and
                     node.test.left.id == '__name__'):
            # Ignore ``__name__ == '__main__'``, since it may be
            # used inside a PyScript file for the compiling.
            return []
        
        code = [self.lf('if (')]  # first part (popped in elif parsing)
        code += self.parse(node.test)
        code.append(') {')
        self._indent += 1
        for stmt in node.body:
            code += self.parse(stmt)
        self._indent -= 1
        if node.orelse:
            if len(node.orelse) == 1 and isinstance(node.orelse[0], ast.If):
                code.append(self.lf("} else if ("))
                code += self.parse(node.orelse[0])[1:-1]  # skip first and last
            else:
                code.append(self.lf("} else {"))
                self._indent += 1
                for stmt in node.orelse:
                    code += self.parse(stmt)
                self._indent -= 1
        code.append(self.lf("}"))  # last part (popped in elif parsing)
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
            code.append(self.lf('%s = true;' % else_dummy))
        
        # Declare iteration variable if necessary
        if target not in self.vars:
            self.vars.add(target)
        if target2 and target2 not in self.vars:
            self.vars.add(target2)
        
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
            code.append(self.lf('%s = %s;' % (d_seq, iter)))
            # The loop
            code += self.lf(), 'for (', target, ' in ', d_seq, ') {'
            self._indent += 1
            code.append(self.lf('if (!%s.hasOwnProperty(%s)){ continue; }' %
                                (d_seq, target)))
            # Set second/alt iteration variable
            if target2:
                code.append(self.lf('%s = %s[%s];' % (target2, d_seq, target)))
        
        else:  # Enumeration
            
            # todo: since we have xx.keys -> Object.keys(xx)
            # we no longer detect the keys enumeration, is that a problem?
            
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
            code.append(self.lf('%s = %s;' % (d_seq, iter)))
            
            # Replace sequence with dict keys if its a dict
            # Note that Object.keys() only yields own enumerable properties
            code.append(self.lf('if ((typeof %s === "object") && '
                                '(!Array.isArray(%s))) {' % (d_seq, d_seq)))
            
            code.append(self.lf('    %s = Object.keys(%s);' % (d_seq, d_seq)))
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
            code.append(self.lf('%s = true;' % else_dummy))
        
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
    
    ## Functions and class definitions
    
    def parse_FunctionDef(self, node, lambda_=False):
        # Common code for the FunctionDef and Lambda nodes.
        
        # Init function definition
        code = []
        if not lambda_:
            prefixed = self.with_prefix(node.name)
            if prefixed == node.name:  # normal function vs method
                self.vars.add(node.name)
            code.append(self.lf('%s = ' % prefixed))
            #code.append('function %s (' % node.name)
            code.append('function (')
        else:
            code.append('function (')
        
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
        if (not lambda_) and node.decorator_list:
            raise JSError('No support for function decorators')
        if node.args.kwonlyargs:
            raise JSError('No support for keyword only arguments')
        if node.args.kwarg:
            raise JSError('No support for kwargs')
        
        # Prepare for content
        code.append(') {')
        pre_code, code = code, []
        self._indent += 1
        self.push_stack('function', '' if lambda_ else node.name)
        
        # Add argnames to known vars
        for name in argnames:
            self.vars.add(name)
        
        # Apply defaults
        offset = len(argnames) - len(node.args.defaults)
        for name, default in zip(argnames[offset:], node.args.defaults):
            d = ''.join(self.parse(default))
            x = '%s = (%s === undefined) ? %s: %s;' % (name, name, d, name)
            code.append(self.lf(x))
        
        # Handle varargs
        if node.args.vararg:
            asarray = 'Array.prototype.slice.call(arguments)'
            name = node.args.vararg.arg
            self.vars.add(name)
            if not argnames:
                # Make available under *arg name
                #code.append(self.lf('%s = arguments;' % name))
                code.append(self.lf('%s = %s;' % (name, asarray)))
            else:
                # Slice it
                code.append(self.lf('%s = %s.slice(%i);' %
                            (name, asarray, len(argnames))))
        # Apply content
        if lambda_:
            code.append('return ')
            code += self.parse(node.body)
            code.append(';')
        else:
            docstring = self.pop_docstring(node)
            if docstring and not node.body:
                # Raw JS
                for line in docstring.splitlines():
                    code.append(self.lf(line))
            else:
                # Normal function
                for line in docstring.splitlines():
                    code.append(self.lf('// ' + line))
                for child in node.body:
                    code += self.parse(child)
        
        # Wrap up
        self._indent -= 1
        if lambda_:
            code.append('}')
        else:
            code.append(self.lf('};\n'))
            # Pop stack, declare vars, but exclude our argnames
            ns = self.pop_stack()
            for name in argnames:
                ns.discard(name)
            if ns:
                dec = 'var ' + ', '.join(sorted(ns)) + ';'
                pre_code.append(self.lf('    ' + dec))
        
        return pre_code + code
    
    def parse_Lambda(self, node):
        return self.parse_FunctionDef(node, True)
    
    def parse_arg(self, node):
        # Py3k only
        name = node.arg
        return self.NAME_MAP.get(name, name)
    
    def parse_Return(self, node):
        if node.value is not None:
            code = [self.lf('return ')]
            code += self.parse(node.value)
            code.append(';')
            return code
        else:
            return self.lf("return;")
    
    def parse_ClassDef(self, node):
        
        # Checks
        for base in node.bases:
            if not isinstance(base, ast.Name):
                raise JSError('Base classes must be simple names.')
        if len(node.bases) > 1:
            raise JSError('Multiple inheritance not (yet) supported.')
        if node.keywords or node.starargs or node.kwargs:
            raise JSError('Metaclasses not supported.')
        if node.decorator_list:
            raise JSError('Class decorators not supported.')
        
        # Get base class (not the constructor)
        base_class = node.bases[0].id if node.bases else 'Object'
        if base_class.lower() == 'object':  # maybe Python "object"
            base_class = 'Object'
        else:
            base_class = base_class + '.prototype'
        
        # Write constructor
        code = []
        code.append(self.lf('%s = function () {' % node.name))
        for line in self.pop_docstring(node).splitlines():
            code.append(self.lf('    // ' + line))
        code.append(self.lf('    if (this.__init__) {'))
        code.append(self.lf('       this.__init__.apply(this, arguments);'))
        code.append(self.lf('    }'))
        code.append(self.lf('};'))
        
        # Apply inheritance
        if base_class != 'Object':
            code.append(self.lf('%s.prototype = Object.create(%s);' %
                                (node.name, base_class)))
        code.append(self.lf('%s.prototype._base_class = %s;' %
                            (node.name, base_class)))
        code.append('\n')
        
        # Body ...
        self.vars.add(node.name)
        self.push_stack('class', node.name)
        for sub in node.body:
            code += self.parse(sub)
        code.append('\n')
        self.pop_stack()
        # no need to declare variables, because they're prefixed
        
        return code
    
    def function_super(self, node):
        # allow using super() in methods
        if node.args:
            raise JSError('super() accepts 0 or 1 arguments.')
        if len(self._stack) < 3:  # module, class, function
            raise JSError('can only use super() inside a method.')
        
        # Find the class of this function. We could also use
        # this._base_class, but by using the class, we mimic Python better.
        nstype1, nsname1, _ = self._stack[-1]
        nstype2, nsname2, _ = self._stack[-2]
        if not (nstype1 == 'function' and nstype2 == 'class'):
            raise JSError('can only use super() inside a method.')
        
        base_class = nsname2
        return '%s.prototype._base_class' % base_class
    
    
    #def parse_With
    #def parse_Withitem
    
    #def parse_Yield
    #def parse_YieldFrom
    #def parse_Global
    #def parse_NonLocal
