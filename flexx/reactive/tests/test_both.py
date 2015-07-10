""" Tests that should run in both Python and JS.
This helps ensure that both implementation work in the same way.
"""

from pytest import raises
from flexx.util.testing import run_tests_if_main

from flexx.reactive import input, signal, react, source, HasSignals
from flexx.reactive.pyscript import create_js_signals_class, HasSignalsJS
from flexx.pyscript import js, evaljs, evalpy


def run_in_both(cls, reference):
    
    if reference.lower() != reference:
        raise ValueError('Test reference should be lowercase!')
    
    def wrapper(func):
        def runner():
            # Run in Python
            pyresult = str(func(cls))
            assert pyresult.lower() == reference
            # Run in JS
            code = HasSignalsJS.jscode
            code += create_js_signals_class(cls, cls.__name__)
            code += 'var test = ' + js(func).jscode
            code += 'test(%s);' % cls.__name__
            jsresult = evaljs(code)
            jsresult = jsresult.replace('[ ', '[').replace(' ]', ']')
            assert jsresult.lower() == reference
        return runner
    return wrapper


class Foo(HasSignals):
    
    def __init__(self):
        self.r = []
        super().__init__()
    
    @input
    def title(v=''):
        #print('asdasd')
        return v
    
    @signal('title')
    def title_len(v):
        return len(v)
    
    @react('title_len')
    def show_title(self, v):
        self.r.append(v)


@run_in_both(Foo, '[0, 2]')
def test_simple(Foo):
    foo = Foo()
    foo.title('xx')
    return foo.r


run_tests_if_main()


