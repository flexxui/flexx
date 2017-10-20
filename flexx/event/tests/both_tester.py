"""
This module defines a utility to write tests for flexx.event
that run both in Python and JS.
"""

import io
import sys

from flexx import event
from flexx.event import loop
from flexx.event._js import create_js_component_class, JS_EVENT
from flexx.pyscript.functions import py2js, evaljs 
from flexx.pyscript.stdlib import get_std_info, get_partial_std_lib


def this_is_js():
    return False


def call_pyfunc(func):
    """ Call a function and capture ints stdout.
    """
    orig_stdout = sys.stdout
    fake_stdout = io.StringIO()
    sys.stdout = fake_stdout
    try:
        func()
    finally:
        sys.stdout = orig_stdout
    return fake_stdout.getvalue()


def smart_compare(text1, text2, what=''):
    """ Compare two texts, raising an error that shows where the texts differ.
    """
    lines1 = text1.splitlines()
    lines2 = text2.splitlines()
    n = max(len(lines1), len(lines2))
    
    while len(lines1) < n:
        lines1.append('<empty>')
    while len(lines2) < n:
        lines2.append('<empty>')
    
    for i in range(n):
        line1, line2 = lines1[i], lines2[i]
        line1 = line1.lower()
        line2 = line2.lower()
        if line1 != line2:
            i1 = max(0, i - 3)
            i2 = min(n, i + 3)
            msg = ''
            for j in range(i1, i2):
                linenr = str(j + 1).rjust(2, '0')
                prefix = ' >> ' if j == i else '    '
                msg += prefix + linenr + ' ' + lines1[j].replace(' ', '\xb7') + '\n'
                msg += prefix + linenr + ' ' + lines2[j].replace(' ', '\xb7') + '\n'
            raise ValueError('Text %s mismatch:\n%s ' % (what, msg))


def run_in_both(*classes):
    """ Decorator to run a test in both Python and JS.
    
    The decorator should be provided with any Component classes that
    you want to use in the test.
    
    The function docstring should match the stdout of the test (case
    insensitive). To provide separate reference outputs for Python and
    JavaScript, use a delimiter of at least 10 '-' characters.
    """
    
    def wrapper(func):
        reference = '\n'.join(line[4:] for line in func.__doc__.splitlines())
        parts = reference.split('-'*10)
        pyref = parts[0].strip(' \n')
        jsref = parts[-1].strip(' \n-')
        
        def runner():
            # Collect base classes
            all_classes = []
            for cls in classes:
                for c in cls.mro():
                    if c is event.Component or c in all_classes:
                        break
                    all_classes.append(c)
            # Generate JS code
            code = JS_EVENT
            for c in reversed(all_classes):
                code += create_js_component_class(c, c.__name__,
                                                  c.__bases__[0].__name__+'.prototype')
            code += py2js(func, 'test', inline_stdlib=False, docstrings=False)
            
            # code += 'console.log(test(%s));' % cls.__name__
            code += 'test();'
            
            nargs, function_deps, method_deps = get_std_info(code)
            code = get_partial_std_lib(function_deps, method_deps, []) + code
            # Run in Python
            pyresult = call_pyfunc(func)
            pyresult = pyresult.replace('"', "'").replace("\\'", "'").split('!!!!')[-1]
            # Run in JS
            jsresult = evaljs(code, print_result=False)  # allow using file
            jsresult = jsresult.replace('[ ', '[').replace(' ]', ']')
            jsresult = jsresult.replace('\n  ', ' ')
            jsresult = jsresult.replace('"', "'").split('!!!!')[-1]
            # Compare
            smart_compare(pyresult, pyref, func.__name__ + '() py')
            smart_compare(jsresult, jsref, func.__name__ + '() js')
            print(func.__name__, 'ok')
        return runner
    return wrapper


class Person(event.Component):
   
    first_name = event.StringProp('John', settable=True)
    last_name = event.StringProp('Doe', settable=True)


@run_in_both(Person)
def test_ok1():
    """
    john doe
    john doe
    almar klein
    """
    p = Person()
    print(p.first_name, p.last_name)
    p.set_first_name('almar')
    p.set_last_name('klein')
    print(p.first_name, p.last_name)
    loop.iter()
    print(p.first_name, p.last_name)


@run_in_both(Person)
def test_ok2():
    """
    bar
    ----------
    foo
    """
    if this_is_js():
        print('foo')
    else:
        print('bar')


@run_in_both(Person)
def test_fail():
    """
    john doe
    almar klein
    """
    p = Person()
    print(p.first_name, p.last_name)
    p.set_first_name('almar')
    p.set_last_name('klein')
    print(p.first_name, p.last_name)
    loop.iter()
    print(p.first_name, p.last_name)


if __name__ == '__main__':
    # Run this as a script to 
    test_ok1()
    test_ok2()
    test_fail()  # this is supposed to fail
