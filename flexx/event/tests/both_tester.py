from flexx.util.testing import run_tests_if_main, raises

from flexx import event
from flexx.event import loop
from flexx.event._js import create_js_component_class, ComponentJS, reprs
from flexx.pyscript.functions import py2js, evaljs, evalpy, js_rename
from flexx.pyscript.stdlib import get_std_info, get_partial_std_lib

import os
import sys
from math import isnan as isNaN

def this_is_js():
    return False


def run_in_both(*classes):
    """ The test decorator.
    """
    
    if reference.lower() != reference:
        raise ValueError('Test reference should be lowercase!')
    
    def wrapper(func):
        def runner():
            # Collect classes
            this_classes = []
            for cls in classes:
                this_classes.append(cls)
                for c in cls.mro():
                    if c is event.Component:
                        break
                    this_classes.append(c)
            print(this_classes)
            # Generate JS code
            code = ComponentJS.JSCODE
            for c in reversed(this_classes):
                code += create_js_component_class(c, c.__name__, c.__bases__[0].__name__+'.prototype')
            code += py2js(func, 'test', inline_stdlib=False, docstrings=False)
            code += 'console.log(test(%s));' % cls.__name__
            nargs, function_deps, method_deps = get_std_info(code)
            code = get_partial_std_lib(function_deps, method_deps, []) + code
            # Run in JS
            jsresult = evaljs(code, print_result=False)  # allow using file
            jsresult = jsresult.replace('[ ', '[').replace(' ]', ']').replace('\n  ', ' ')
            jsresult = jsresult.replace('"', "'").split('!!!!')[-1]
            print('js:', jsresult)
            # Run in Python
            pyresult = reprs(func(cls))
            pyresult = pyresult.replace('"', "'").replace("\\'", "'").split('!!!!')[-1]
            print('py:', pyresult)
            # Compare
            assert pyresult.lower() == reference
            assert jsresult.lower() == reference
        return runner
    return wrapper


class Person(event.Component):
    
    _foo = 3
    _bar = 'bar'
    spam = [1, 2, 3]
    
    first_name = event.StringProp('')
    age = event.IntProp(0)


##

@run_in_both(Person)
def test_name():
    """
    
    ------------------------------------------
    
    """
    # todo: in docstting instead?
    p = Person()
    p.set_first_name('almar')
    p.set_last_name('klein')
    loop.iter()

##


test_name()
