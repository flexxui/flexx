"""
Tests that should run in both Python and JS.
This helps ensure that both implementation work in the same way.

Focus on use-cases rather than coverage.

These tests work a bit awkward, but its very useful to be able to test
that the two systems work exactly the same way. You define a HasEvents
class, and then provide that class to a test function using a
decorator. The test function will then be run both in Python and in JS.
The test function should return an object, that when evaluated to a
string matches with the reference string given to the decorator. The
result string is made lowercase, and double quotes are converted to
single quotes.
"""

from flexx.util.testing import run_tests_if_main, raises

from flexx import event
from flexx.event._pyscript import create_js_hasevents_class, HasEventsJS, reprs
from flexx.pyscript.functions import py2js, evaljs, evalpy, js_rename
from flexx.pyscript.stdlib import get_std_info, get_partial_std_lib



# todo: --\
# Test that multiple handlers get the same event object 
# Test dynamism
# undefined fix, necessary?
# rename _pyscript to "js" or at least something public?


def run_in_both(cls, reference, extra_classes=()):
    """ The test decorator.
    """
    
    if reference.lower() != reference:
        raise ValueError('Test reference should be lowercase!')
    
    def wrapper(func):
        def runner():
            # Run in JS
            code = HasEventsJS.JSCODE #js_rename(HasEventsJS.JSCODE, 'HasEventsJS', 'HasEvents')
            for c in cls.mro()[1:]:
                if c is event.HasEvents:
                    break
                code += create_js_hasevents_class(c, c.__name__, c.__bases__[0].__name__+'.prototype')
            for c in extra_classes:
                code += create_js_hasevents_class(c, c.__name__)
            code += create_js_hasevents_class(cls, cls.__name__, cls.__bases__[0].__name__+'.prototype')
            code += py2js(func, 'test', inline_stdlib=False)
            code += 'test(%s);' % cls.__name__
            nargs, function_deps, method_deps = get_std_info(code)
            code = get_partial_std_lib(function_deps, method_deps, []) + code
            jsresult = evaljs(code)
            jsresult = jsresult.replace('[ ', '[').replace(' ]', ']')
            jsresult = jsresult.replace('"', "'")
            print('js:', jsresult)
            # Run in Python
            pyresult = reprs(func(cls))
            pyresult = pyresult.replace('"', "'").replace("\\'", "'")
            print('py:', pyresult)
            #
            assert pyresult.lower() == reference
            assert jsresult.lower() == reference
        return runner
    return wrapper


class Name(event.HasEvents):
    
    _foo = 3
    _bar = 'bar'
    spam = [1, 2, 3]
    
    def __init__(self):
        self.r = []
        super().__init__()
    
    @event.prop
    def first_name(self, v='john'):
        return str(v)
    
    @event.prop
    def last_name(self, v='doe'):
        return str(v)
    
    @event.readonly
    def full_name(self, v=''):
        return str(v)
    
    @event.connect('first_name', 'last_name')
    def _set_full_name(self, *events):
        self.r.append('')
        self._set_prop('full_name', self.first_name + ' ' + self.last_name)


@run_in_both(Name, "['', 'john doe', '', 'almar klein', '', 'jorik klein']")
def test_name(Name):
    name = Name()
    name._set_full_name.handle_now()
    name.r.append(name.full_name)
    name.first_name = 'almar'
    name.last_name = 'klein'
    name._set_full_name.handle_now()
    name.r.append(name.full_name)
    name.first_name = 'jorik'
    name._set_full_name.handle_now()
    name.r.append(name.full_name)
    return name.r


# run_tests_if_main()
test_name()

