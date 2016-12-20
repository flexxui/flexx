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

While loops map well to JS

.. pyscript_example::

    val = 0
    while val < 10:
        val += 1

Explicit iterating over arrays (and strings):

.. pyscript_example::

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


Iterations over dicts:

.. pyscript_example::

    # Plain iteration over a dict has a minor overhead
    for key in d:
        print(key)
    
    # Which is why we recommend using keys(), values(), or items()
    for key in d.keys():
        print(key)
    
    for val in d.values():
        print(val)
    
    for key, val in d.items():
        print(key, val, sep=': ')


We can iterate over anything:

.. pyscript_example::

    # Strings
    for char in "foo bar":
        print(c)
    
    # More complex data structes
    for i, j in [[1, 2], [3, 4]]:
        print(i+j)

Buildin functions intended for iterations are supported too: 
enumerate, zip, reversed, sorted, filter, map.

.. pyscript_example::

    for i, x in enumerate(foo):
        pass
    
    for a, b in zip(foo, bar):
        pass
    
    for x in reversed(sorted(foo)):
        pass
    
    for x in map(lambda x: x+1, foo):
        pass
    
    for x in filter(lambda x: x>0, foo):
        pass


Comprehensions
--------------

.. pyscript_example::
    
    # List comprehensions just work
    x = [i*2 for i in some_array if i>0]
    y = [i*j for i in a for j in b]


Defining functions
------------------

.. pyscript_example::

    def display(val):
        print(val)
    
    # Support for *args
    def foo(x, *values):
        bar(x+1, *values)
    
    # To write the function in raw JS, use the RawJS call
    def bar(a, b):
        RawJS('''
        var c = 4;
        return a + b + c;
        ''')
    
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
        def add1(self):
            self.x += 1
    
    # Methods are bound functions, like in Python
    b = Bar()
    setTimeout(b.add1, 1000)
    
    # Functions defined in methods (and that do not start with self or this)
    # have ``this`` bound the the same object.
    class Spam(Bar):
        def add_later(self):
            setTimeout(lambda ev: self.add1(), 1000)


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

Globals and nonlocal
--------------------

.. pyscript_example::
    
    a = 3
    def foo():
        global a
        a = 4
    foo()
    # a is now 4

"""

from . import commonast as ast
from . import stdlib
from . import logger
from .parser1 import Parser1, JSError, unify, reprs  # noqa


RAW_DOC_WARNING = ('Function %s only has a docstring, which used to be '
                   'intepreted as raw JS. Wrap a call to RawJS(...) around the '
                   'docstring, or add "pass" to the function body to prevent '
                   'this behavior.')

JS_RESERVED_WORDS = set()


# https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Lexical_grammar
RESERVED = {'true', 'false', 'null',
            # Reserved keywords as of ECMAScript 6
            'break', 'case', 'catch', 'class', 'const', 'continue', 'debugger',
            'default', 'delete', 'do', 'else', 'export', 'extends', 'finally',
            'for', 'function', 'if', 'import', 'in', 'instanceof', 'new',
            'return', 'super', 'switch', 'this', 'throw', 'try', 'typeof',
            'var', 'void', 'while', 'with', 'yield',
            # Future reserved keywords
            'implements', 'interface', 'let', 'package', 'private',
            'protected', 'public', 'static', 'enum',
            'await',  # only in module code
            }

 
class Parser2(Parser1):
    """ Parser that adds control flow, functions, classes, and exceptions.
    """
    
    ## Exceptions
    
    def parse_Raise(self, node):
        # We raise the exception as an Error object
        
        if node.exc_node is None:
            raise JSError('When raising, provide an error object.')
        if node.cause_node is not None:
            raise JSError('When raising, "cause" is not supported.')
        err_node = node.exc_node
        
        # Get cls and msg
        err_cls, err_msg = None, "''"
        if isinstance(err_node, ast.Name):
            if err_node.name[0].islower():  # raise an (error) object
                return [self.lf("throw " + err_node.name + ';')]
            err_cls = err_node.name
        elif isinstance(err_node, ast.Call):
            err_cls = err_node.func_node.name
            err_msg = ''.join([unify(self.parse(arg)) for arg in err_node.arg_nodes])
        else:
            err_msg = ''.join(self.parse(err_node))
        
        err_name = 'err_%i' % self._indent
        self.vars.add(err_name)
        
        # Build code to throw
        code = []
        if err_cls:
            code.append(self.lf("%s = " % err_name))
            code.append('new Error(')
            code.append("'%s:' + " % err_cls)
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
        
        test = ''.join(self.parse(node.test_node))
        msg = test
        if node.msg_node:
            msg = ''.join(self.parse(node.msg_node))
        
        code = []
        code.append(self.lf('if (!('))
        code += test
        code.append(')) {')
        code.append('throw "AssertionError: " + ')  # don't bother with new Error
        code.append(reprs(msg))
        code.append(";}")
        return code
    
    def parse_Try(self, node):
        if node.else_nodes:
            raise JSError('No support for try-else clause.')
        
        code = []
        
        # Try
        if True:
            code.append(self.lf('try {'))
            self._indent += 1
            for n in node.body_nodes:
                code += self.parse(n)
            self._indent -= 1
            code.append(self.lf('}'))
        
        # Except
        if node.handler_nodes:
            self._indent += 1
            err_name = 'err_%i' % self._indent
            code.append(' catch(%s) {' % err_name)
            for i, handler in enumerate(node.handler_nodes):
                if i == 0:
                    code.append(self.lf(''))
                else:
                    code.append(' else ')
                code += self.parse(handler)
            
            self._indent -= 1
            code.append(self.lf('}'))  # end catch
        
        # Finally
        if node.finally_nodes:
            code.append(' finally {')
            self._indent += 1
            for n in node.finally_nodes:
                code += self.parse(n)
            self._indent -= 1
            code.append(self.lf('}'))  # end finally
        
        return code
        
    def parse_ExceptHandler(self, node):
        err_name = 'err_%i' % self._indent
        
        # Setup the catch
        code = []
        err_type = unify(self.parse(node.type_node)) if node.type_node else ''
        self.vars.discard(err_type)
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
        for n in node.body_nodes:
            code += self.parse(n)
        self._indent -= 1
        
        code.append(self.lf('}'))
        return code
    
    ## Control flow
    
    def parse_IfExp(self, node):
        # in "a if b else c"
        a = self.parse(node.body_node)
        b = self._wrap_truthy(node.test_node)
        c = self.parse(node.else_node)
        
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
        if (True and isinstance(node.test_node, ast.Compare) and
                     isinstance(node.test_node.left_node, ast.Name) and
                     node.test_node.left_node.name == '__name__'):
            # Ignore ``__name__ == '__main__'``, since it may be
            # used inside a PyScript file for the compiling.
            return []
        
        # Shortcut for this_is_js() cases, discarting the else to reduce code
        if (True and isinstance(node.test_node, ast.Call) and
                     isinstance(node.test_node.func_node, ast.Name) and
                     node.test_node.func_node.name == 'this_is_js'):
            code = [self.lf('{ /* if this_is_js() */')]
            for stmt in node.body_nodes:
                code += self.parse(stmt)
            code.append(self.lf('}'))
            return code
        
        # Disable body if "not this_is_js()"
        if (True and isinstance(node.test_node, ast.UnaryOp) and
                     node.test_node.op == 'Not' and
                     isinstance(node.test_node.right_node, ast.Call) and
                     isinstance(node.test_node.right_node.func_node, ast.Name) and
                     node.test_node.right_node.func_node.name == 'this_is_js'):
            node.body_nodes = []
        
        code = [self.lf('if (')]  # first part (popped in elif parsing)
        code.append(self._wrap_truthy(node.test_node))
        code.append(') {')
        self._indent += 1
        for stmt in node.body_nodes:
            code += self.parse(stmt)
        self._indent -= 1
        if node.else_nodes:
            if len(node.else_nodes) == 1 and isinstance(node.else_nodes[0], ast.If):
                code.append(self.lf("} else if ("))
                code += self.parse(node.else_nodes[0])[1:-1]  # skip first and last
            else:
                code.append(self.lf("} else {"))
                self._indent += 1
                for stmt in node.else_nodes:
                    code += self.parse(stmt)
                self._indent -= 1
        code.append(self.lf("}"))  # last part (popped in elif parsing)
        return code
    
    def parse_For(self, node):
        # Note that enumerate, reversed, sorted, filter, map are handled in parser3
        
        METHODS = 'keys', 'values', 'items'
        
        iter = None  # what to iterate over
        sure_is_dict = False  # flag to indicate that we're sure iter is a dict
        sure_is_range = False  # dito for range
        
        # First see if this for-loop is something that we support directly
        if isinstance(node.iter_node, ast.Call):
            f = node.iter_node.func_node
            if (isinstance(f, ast.Attribute) and
                    not node.iter_node.arg_nodes and f.attr in METHODS):
                sure_is_dict = f.attr
                iter = ''.join(self.parse(f.value_node))
            elif isinstance(f, ast.Name) and f.name in ('xrange', 'range'):
                sure_is_range = [''.join(self.parse(arg)) for arg in 
                                 node.iter_node.arg_nodes]
        
        # Otherwise we parse the iter
        if iter is None:
            iter = ''.join(self.parse(node.iter_node))
        
        # Get target
        if isinstance(node.target_node, ast.Name):
            target = [node.target_node.name]
            if sure_is_dict == 'values':
                target.append(target[0])
            elif sure_is_dict == 'items':
                raise JSError('Iteration over a dict with .items() '
                              'needs two iterators.')
        elif isinstance(node.target_node, ast.Tuple):
            target = [''.join(self.parse(t)) for t in node.target_node.element_nodes]
            if sure_is_dict:
                if not (sure_is_dict == 'items' and len(target) == 2):
                    raise JSError('Iteration over a dict needs one iterator, '
                                  'or 2 when using .items()')
            elif sure_is_range:
                raise JSError('Iterarion via range() needs one iterator.')
        else:
            raise JSError('Invalid iterator in for-loop')
        
        # Collect body and else-body
        for_body = []
        for_else = []
        self._indent += 1
        for n in node.body_nodes:
            for_body += self.parse(n)
        for n in node.else_nodes:
            for_else += self.parse(n)
        self._indent -= 1
        
        # Init code
        code = []
        
        # Prepare variable to detect else
        if node.else_nodes:
            else_dummy = self.dummy('els')
            code.append(self.lf('%s = true;' % else_dummy))
        
        # Declare iteration variables if necessary
        for t in target:
            self.vars.add(t)
        
        if sure_is_range:  # Explicit iteration
            # Get range args
            nums = sure_is_range  # The range() arguments
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
            assert len(target) == 1
            t = t.format(i=target[0], start=start, end=end, step=step) + ' {'
            code.append(self.lf(t))
            self._indent += 1
        
        elif sure_is_dict:  # Enumeration over an object (i.e. a dict)
            # Create dummy vars
            d_seq = self.dummy('seq')
            code.append(self.lf('%s = %s;' % (d_seq, iter)))
            # The loop
            code += self.lf(), 'for (', target[0], ' in ', d_seq, ') {'
            self._indent += 1
            code.append(self.lf('if (!%s.hasOwnProperty(%s)){ continue; }' %
                                (d_seq, target[0])))
            # Set second/alt iteration variable
            if len(target) > 1:
                code.append(self.lf('%s = %s[%s];' % (target[1], d_seq, target[0])))
        
        else:  # Enumeration
            
            # We cannot know whether the thing to iterate over is an
            # array or a dict. We use a for-iterarion (otherwise we
            # cannot be sure of the element order for arrays). Before
            # running the loop, we test whether its an array. If its
            # not, we replace the sequence with the keys of that
            # sequence. Peformance for arrays should be good. For
            # objects probably slightly less.
            
            # Create dummy vars
            d_seq = self.dummy('seq')
            d_iter = self.dummy('itr')
            d_target = target[0] if (len(target) == 1) else self.dummy('tgt')
            
            # Ensure our iterable is indeed iterable
            code.append(self._make_iterable(iter, d_seq))
            
            # The loop
            code.append(self.lf('for (%s = 0; %s < %s.length; %s += 1) {' %
                                (d_iter, d_iter, d_seq, d_iter)))
            self._indent += 1
            code.append(self.lf('%s = %s[%s];' % (d_target, d_seq, d_iter)))
            if len(target) > 1:
                code.append(self.lf(self._iterator_assign(d_target, *target)))
        
        # The body of the loop
        code += for_body
        self._indent -= 1
        code.append(self.lf('}'))
        
        # Handle else
        if node.else_nodes:
            code.append(' if (%s) {' % else_dummy)
            code += for_else
            code.append(self.lf("}"))
            # Update all breaks to set the dummy. We overwrite the
            # "break;" so it will not be detected by a parent loop
            ii = [i for i, part in enumerate(code) if part=='break;']
            for i in ii:
                code[i] = '%s = false; break;' % else_dummy
        
        return code
    
    def _make_iterable(self, name1, name2, newlines=True):
        code = []
        lf = self.lf
        if not newlines:  # pragma: no cover
            lf = lambda x: x
        
        if name1 != name2:
            code.append(lf('%s = %s;' % (name2, name1)))
        code.append(lf('if ((typeof %s === "object") && '
                       '(!Array.isArray(%s))) {' % (name2, name2)))
        code.append(lf('    %s = Object.keys(%s);' % (name2, name2)))
        code.append(lf('}'))
        return ''.join(code)
    
    def parse_While(self, node):
        
        test = ''.join(self.parse(node.test_node))
        
        # Collect body and else-body
        for_body = []
        for_else = []
        self._indent += 1
        for n in node.body_nodes:
            for_body += self.parse(n)
        for n in node.else_nodes:
            for_else += self.parse(n)
        self._indent -= 1
        
        # Init code
        code = []
        
        # Prepare variable to detect else
        if node.else_nodes:
            else_dummy = self.dummy('els')
            code.append(self.lf('%s = true;' % else_dummy))
        
        # The loop itself
        code.append(self.lf("while (%s) {" % test))
        self._indent += 1
        code += for_body
        self._indent -= 1
        code.append(self.lf('}'))
        
        # Handle else
        if node.else_nodes:
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
    
    ## Comprehensions
    
    def parse_ListComp(self, node):
        
        self.push_stack('function', 'listcomp')
        elt = ''.join(self.parse(node.element_node))
        code = ['(function list_comprehension () {', 'var res = [];']
        vars = []
        
        for iter, comprehension in enumerate(node.comp_nodes):
            cc = []
            # Get target (can be multiple vars)
            if isinstance(comprehension.target_node, ast.Tuple):
                target = [''.join(self.parse(t)) for t in 
                          comprehension.target_node.element_nodes]
            else:
                target = [''.join(self.parse(comprehension.target_node))]
            for t in target:
                vars.append(t)
            # comprehension(target_node, iter_node, if_nodes)
            cc.append('iter# = %s;' % ''.join(self.parse(comprehension.iter_node)))
            cc.append('if ((typeof iter# === "object") && '
                      '(!Array.isArray(iter#))) {iter# = Object.keys(iter#);}')
            cc.append('for (i#=0; i#<iter#.length; i#++) {')
            cc.append(self._iterator_assign('iter#[i#]', *target))
            # Ifs
            if comprehension.if_nodes:
                cc.append('if (!(')
                for iff in comprehension.if_nodes:
                    cc += unify(self.parse(iff))
                    cc.append('&&')
                cc.pop(-1)  # pop '&&'
                cc.append(')) {continue;}')
            # Insert code for this comprehension loop
            code.append(''.join(cc).replace('i#', 'i%i' % iter).replace(
                                            'iter#', 'iter%i' % iter))
            vars.extend(['iter%i' % iter, 'i%i' % iter])
        # Push result
        code.append('{res.push(%s);}' % elt)
        for comprehension in node.comp_nodes:
            code.append('}')  # end for
        # Finalize
        code.append('return res;})')  # end function
        code.append('.apply(this)')  # call function
        code.insert(2, 'var %s;' % ', '.join(vars))
        # Clean vars
        for var in vars:
            self.vars.add(var)
        self.pop_stack()
        return code
        
        # todo: apply the apply(this) trick everywhere where we use a function
    # SetComp
    # GeneratorExp
    # DictComp
    # comprehension
    
    def _iterator_assign(self, val, *names):
        if len(names) == 1:
            return '%s = %s;' % (names[0], val)
        else:
            code = []
            for i, name in enumerate(names):
                code.append('%s = %s[%i];' % (name, val, i))
            return ' '.join(code)
    
    ## Functions and class definitions
    
    def parse_FunctionDef(self, node, lambda_=False):
        # Common code for the FunctionDef and Lambda nodes.
        
        has_self = node.arg_nodes and node.arg_nodes[0].name in ('self', 'this')
        
        # Bind if this function is inside a function, and does not have self
        binder = ''  # code to add to the end
        if len(self._stack) >= 1 and self._stack[-1][0] == 'function':
            if not has_self:
                binder = ').bind(this)'
        
        # Init function definition
        # Non-anonymouse functions get a name so that they are debugged more
        # easily and resolve to the correct event labels in flexx.event. However,
        # we cannot use the exact name, since we don't want to actually *use* it.
        # Classes give their methods a __name__, so no need to name these.
        code = []
        func_name = ''
        if not lambda_:
            if not has_self:
                func_name = 'flx_' + node.name
            prefixed = self.with_prefix(node.name)
            if prefixed == node.name:  # normal function vs method
                self.vars.add(node.name)
                self._seen_func_names.add(node.name)
            code.append(self.lf('%s = ' % prefixed))
        code.append('%sfunction %s%s(' % ('(' if binder else '',
                                          func_name,
                                          ' ' if func_name else ''))
        
        # Collect args
        argnames = []
        for arg in node.arg_nodes:  # ast.Arg nodes
            name = self.NAME_MAP.get(arg.name, arg.name)
            if name != 'this':
                argnames.append(name)
                # Add code and comma
                code.append(name)
                code.append(', ')
        if argnames:
            code.pop(-1)  # pop last comma
        
        # Check
        if (not lambda_) and node.decorator_nodes:
            if not (len(node.decorator_nodes) == 1 and
                    node.decorator_nodes[0].name == 'staticmethod'):
                raise JSError('No support for function decorators')
        if node.kwarg_nodes:
            raise JSError('No support for keyword only arguments')
        if node.kwargs_node:
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
        for arg in node.arg_nodes:
            if arg.value_node is not None:
                name = arg.name
                d = ''.join(self.parse(arg.value_node))
                x = '%s = (%s === undefined) ? %s: %s;' % (name, name, d, name)
                code.append(self.lf(x))
        
        # Handle varargs
        if node.args_node:
            asarray = 'Array.prototype.slice.call(arguments)'
            name = node.args_node.name  # always an ast.Arg
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
            code += self.parse(node.body_node)
            code.append(';')
        else:
            docstring = self.pop_docstring(node)
            if docstring and not node.body_nodes:
                # Raw JS - but deprecated
                logger.warn(RAW_DOC_WARNING % node.name)
                for line in docstring.splitlines():
                    code.append(self.lf(line))
            else:
                # Normal function
                if self._docstrings:
                    for line in docstring.splitlines():
                        code.append(self.lf('// ' + line))
                for child in node.body_nodes:
                    code += self.parse(child)
        
        # Wrap up
        if lambda_:
            code.append('}%s' % binder)
            # ns should only consist of arg names
            ns = self.pop_stack()
            assert not set(ns).difference(argnames)
        else:
            if not (code and code[-1].strip().startswith('return ')):
                code.append(self.lf('return null;'))
            # Declare vars, but exclude our argnames
            for name in argnames:
                self.vars.discard(name)
            ns = self.pop_stack()
            pre_code.append(self.get_declarations(ns))
        
        self._indent -= 1
        if not lambda_:
            code.append(self.lf('}%s;\n' % binder))
        return pre_code + code
    
    def parse_Lambda(self, node):
        return self.parse_FunctionDef(node, True)
    
    def parse_Return(self, node):
        if node.value_node is not None:
            return self.lf('return %s;' % ''.join(self.parse(node.value_node)))
        else:
            return self.lf("return null;")
    
    def parse_ClassDef(self, node):
        
        # Checks
        if len(node.arg_nodes) > 1:
            raise JSError('Multiple inheritance not (yet) supported.')
        if node.kwarg_nodes:
            raise JSError('Metaclasses not supported.')
        if node.decorator_nodes:
            raise JSError('Class decorators not supported.')
        
        # Get base class (not the constructor)
        base_class = 'Object'
        if node.arg_nodes:
            base_class = ''.join(self.parse(node.arg_nodes[0]))
        if not base_class.replace('.', '_').isalnum():
            raise JSError('Base classes must be simple names')
        elif base_class.lower() == 'object':  # maybe Python "object"
            base_class = 'Object'
        else:
            base_class = base_class + '.prototype'
        
        # Define function that acts as class constructor
        code = []
        docstring = self.pop_docstring(node) 
        docstring = docstring if self._docstrings else ''
        for line in get_class_definition(node.name, base_class, docstring):
            code.append(self.lf(line))
        self.use_std_function('op_instantiate', [])
        
        # Body ...
        self.vars.add(node.name)
        self._seen_class_names.add(node.name)
        self.push_stack('class', node.name)
        for sub in node.body_nodes:
            code += self.parse(sub)
        code.append('\n')
        self.pop_stack()
        # no need to declare variables, because they're prefixed
        
        return code
    
    def function_super(self, node):
        # allow using super() in methods
        # Note that in parse_Call() we ensure that a call using super
        # uses .call(this, ...) so that the instance is handled ok.
        
        if node.arg_nodes:
            #raise JSError('super() accepts 0 or 1 arguments.')
            pass  # In Python 2, arg nodes are provided, and we ignore them
        if len(self._stack) < 3:  # module, class, function
            #raise JSError('can only use super() inside a method.')
            # We just provide "super()" and hope that the user will
            # replace the code (as we do in the Model class).
            return 'super()'
        
        # Find the class of this function. Using this._base_class would work
        # in simple situations, but not when there's two levels of super().
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
    
    def parse_Global(self, node):
        for name in node.names:
            self._globals.append(name)  # Keep track of globals
            self.vars.set_nonlocal(name)
        return '' 
    
    def parse_Nonlocal(self, node):
        for name in node.names:
            self.vars.set_nonlocal(name)
        return '' 


def get_class_definition(name, base='Object', docstring=''):
    """ Get a list of lines that defines a class in JS.
    Used in the parser as well as by flexx.ui.Model.
    """
    code = []
    
    code.append('%s = function () {' % name)
    for line in docstring.splitlines():
        code.append('    // ' + line)
    code.append('    %sop_instantiate(this, arguments);' % stdlib.FUNCTION_PREFIX)
    code.append('}')
    
    if base != 'Object':
        code.append('%s.prototype = Object.create(%s);' % (name, base))
    code.append('%s.prototype._base_class = %s;' % (name, base))
    code.append('%s.prototype._class_name = %s;' % (name, reprs(name.split('.')[-1])))
    
    code.append('')
    return code
