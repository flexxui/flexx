""" Tests that should run in both Python and JS.
This helps ensure that both implementation work in the same way.
"""

from pytest import raises
from flexx.util.testing import run_tests_if_main

from flexx.reactive import input, signal, react, source, HasSignals
from flexx.reactive.pyscript import createHasSignalsClass, HasSignalsJS
from flexx.pyscript import js, evaljs, evalpy


def run_in_both(cls, reference):
    
    if reference.lower() != reference:
        raise ValueError('Test reference should be lowercase!')
    
    def wrapper(func):
        def runner():
            # Run in Python
            # pyresult = str(func(cls))
            # assert pyresult.lower() == reference
            # Run in JS
            code = HasSignalsJS.jscode
            code += createHasSignalsClass(cls, cls.__name__)
            code += 'var test = ' + js(func).jscode
            code += 'test(%s);' % cls.__name__
            jsresult = evaljs(code)
            assert jsresult.lower() == reference
        return runner
    return wrapper


class Foo(HasSignals):
    
    def __init__(self):
        super().__init__()
        self.r = []
    
    @input
    def title(v=''):
        return str(v)
    
    @signal('title')
    def title_len(v):
        return len(v)
    
    @react('title_len')
    def show_title(v):
        self.r.append(v)


@run_in_both(Foo, '[0]')
def test_simple(Foo):
    foo = Foo()
    return foo.title()  # todo:  input must set the value on init ...


run_tests_if_main()


