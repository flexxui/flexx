"""
This module defines a utility to write tests for flexx.event
that run both in Python and JS.

This is part of flexx.event and not in flexx/event/tests because (re)import
during tests.
"""

import sys

from ._loop import loop, this_is_js
from ._component import Component
from ._js import create_js_component_class, JS_EVENT

from ..pyscript.functions import py2js, evaljs 
from ..pyscript.stdlib import get_std_info, get_partial_std_lib


class StdoutMismatchError(Exception):
    """ Raised when the stdout mismatches.
    """
    pass


class FakeStream:
    """ To capture Pythons stdout and stderr during the both-tests.
    """
    
    def __init__(self):
        self._parts = []
    
    def write(self, msg):
        # Keep single messages together, so that errors are compared as one "line"
        msg2 = msg.replace('\n', '\r')
        if msg.endswith('\n'):
            self._parts.append(msg2[:-1] + '\n')
        else:
            self._parts.append(msg2)
    
    def flush(self):
        pass
    
    def getvalue(self):
        return ''.join(self._parts)


def call_func_in_py(func):
    """ Call a function and capture ints stdout.
    """
    loop.reset()
    orig_stdout = sys.stdout
    orig_stderr = sys.stderr
    fake_stdout = FakeStream()
    sys.stdout = sys.stderr = fake_stdout
    try:
        func()
    except Exception as err:
        raise  # fall through
    finally:
        sys.stdout = orig_stdout
        sys.stderr = orig_stderr
    return fake_stdout.getvalue().rstrip()


def call_func_in_js(func, classes, extra_nodejs_args=None):
    # Collect base classes
    all_classes = []
    for cls in classes:
        for c in cls.mro():
            if c is Component or c in all_classes:
                break
            all_classes.append(c)
    # Generate JS code
    code = JS_EVENT
    for c in reversed(all_classes):
        code += create_js_component_class(c, c.__name__,
                                          c.__bases__[0].__name__+'.prototype')
    code += py2js(func, 'test', inline_stdlib=False, docstrings=False)
    code += 'test();'
    nargs, function_deps, method_deps = get_std_info(code)
    code = get_partial_std_lib(function_deps, method_deps, []) + code
    # Call (allow using file)
    return evaljs(code, print_result=False, extra_nodejs_args=extra_nodejs_args)


def smart_compare(kinds, text1, text2, what=''):
    """ Compare two texts, first being the reference,
    raising an error that shows where the texts differ.
    """
    lines1 = text1.split('\n')
    lines2 = text2.split('\n')
    n = max(len(lines1), len(lines2))
    
    while len(lines1) < n:
        lines1.append('<empty>')
    while len(lines2) < n:
        lines2.append('<empty>')
    
    refpfx = '\xaf   '
    
    for i in range(n):
        line1, line2 = lines1[i], lines2[i]
        line1 = line1.lower()
        line2 = line2.lower()
        if line1.startswith('?'):
            equal_enough = line1[1:].strip() in line2
        else:
            equal_enough = line1 == line2
        if not equal_enough:
            i1 = max(0, i - 3)
            i2 = min(n, i + 3)
            msg = ''
            for j in range(i1, i2):
                linenr = str(j + 1).rjust(2, '0')
                prefix = ' >> ' if j == i else '    '
                msg += '{}{} {} {}'.format(refpfx, kinds[0], linenr,
                                           lines1[j].replace(' ', '\xb7') + '\n')
                msg += '{}{} {} {}'.format(prefix, kinds[1], linenr,
                                           lines2[j].replace(' ', '\xb7') + '\n')
            raise StdoutMismatchError('Text mismatch in %s:\n%s ' % (what, msg))

# todo: do I use the split option? If not, compare ref py and js in one go

def run_in_both(*classes, js=True, py=True, extra_nodejs_args=None):
    """ Decorator to run a test in both Python and JS.
    
    The decorator should be provided with any Component classes that
    you want to use in the test.
    
    The function docstring should match the stdout + stderr of the test (case
    insensitive). To provide separate reference outputs for Python and
    JavaScript, use a delimiter of at least 10 '-' characters. Use "? xx"
    to test that "xx" is present on a line (useful for logged exceptions).
    """
    
    def wrapper(func):
        reference = '\n'.join(line[4:] for line in func.__doc__.splitlines())
        parts = reference.split('-'*10)
        pyref = parts[0].strip(' \n')
        jsref = parts[-1].strip(' \n-')
        
        def runner1():
            # One level of indirection to make cleaner error reporting by pytest
            err = None
            try:
                return runner2()
            except Exception as e:
                err = e
            if isinstance(err, StdoutMismatchError):
                raise StdoutMismatchError(err)
            elif isinstance(err, RuntimeError):
                raise RuntimeError(err)
            else:
                raise err
        
        def runner2():
            # Run in Python
            if py:
                pyresult = call_func_in_py(func)
                pyresult = pyresult.replace('"', "'").replace("\\'", "'")
                pyresult = pyresult.split('!!!!')[-1]
                #print('Py:\n' + pyresult)
            # Run in JS
            if js:
                jsresult = call_func_in_js(func, classes, extra_nodejs_args)
                jsresult = jsresult.replace('[ ', '[').replace(' ]', ']')
                jsresult = jsresult.replace('\n  ', ' ')
                jsresult = jsresult.replace('"', "'").split('!!!!')[-1]
                jsresult = jsresult.replace('null', 'None')
                #print('JS:\n' + jsresult)
            if py:
                smart_compare('rp', pyref, pyresult, func.__name__ + '() in Python')
            if js:
                smart_compare('rj', jsref, jsresult, func.__name__ + '() in JavaScript')
            print(func.__name__, 'ok')
            return True
        return runner1
    return wrapper
