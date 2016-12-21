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
from flexx.event import loop
from flexx.event._js import create_js_hasevents_class, HasEventsJS, reprs
from flexx.pyscript.functions import py2js, evaljs, evalpy, js_rename
from flexx.pyscript.stdlib import get_std_info, get_partial_std_lib

import os
import sys
from math import isnan as isNaN

def this_is_js():
    return False


def run_in_both(cls, reference, extra_classes=()):
    """ The test decorator.
    """
    
    if reference.lower() != reference:
        raise ValueError('Test reference should be lowercase!')
    
    def wrapper(func):
        def runner():
            # Run in JS
            code = HasEventsJS.JSCODE
            for c in extra_classes:
                code += create_js_hasevents_class(c, c.__name__)
            this_classes = []
            for c in cls.mro():
                if c is event.HasEvents:
                    break
                this_classes.append(c)
            for c in reversed(this_classes):
                code += create_js_hasevents_class(c, c.__name__, c.__bases__[0].__name__+'.prototype')
            code += py2js(func, 'test', inline_stdlib=False, docstrings=False)
            code += 'console.log(test(%s));' % cls.__name__
            nargs, function_deps, method_deps = get_std_info(code)
            code = get_partial_std_lib(function_deps, method_deps, []) + code
            jsresult = evaljs(code, print_result=False)  # allow using file
            jsresult = jsresult.replace('[ ', '[').replace(' ]', ']').replace('\n  ', ' ')
            jsresult = jsresult.replace('"', "'").split('!!!!')[-1]
            print('js:', jsresult)
            # Run in Python
            pyresult = reprs(func(cls))
            pyresult = pyresult.replace('"', "'").replace("\\'", "'").split('!!!!')[-1]
            print('py:', pyresult)
            #
            assert pyresult.lower() == reference
            assert jsresult.lower() == reference
        return runner
    return wrapper


class Person(event.HasEvents):
    
    _foo = 3
    _bar = 'bar'
    spam = [1, 2, 3]
    
    def __init__(self):
        self.r1 = []
        self.r2 = []
        self.r3 = []
        self.r4 = []
        super().__init__()
    
    @event.prop
    def age(self, v=0):
        v = float(v)
        assert not isNaN(v)  # JS wont fail but make NaN
        return v
    
    @event.readonly
    def nchildren(self, v=0):
        v = int(v)
        assert not isNaN(v)  # JS wont fail but make NaN
        return v
    
    @event.prop
    def first_name(self, v='john'):
        return str(v)
    
    @event.prop
    def last_name(self, v='doe'):
        return str(v)
    
    @event.readonly
    def full_name(self, v=''):
        return str(v)
    
    @event.emitter
    def yell(self, v):
        v = int(v)
        assert not isNaN(v)  # JS wont fail but make NaN
        return {'action': 'yell', 'value': v}
    
    @event.connect('first_name')
    def _first_name_logger(self, *events):
        for ev in events:
            self.r1.append(ev.old_value + '-' + ev.new_value)
    
    @event.connect('full_name')
    def _full_name_logger(self, *events):
        for ev in events:
            self.r2.append(ev.old_value + '-' + ev.new_value)
    
    @event.connect('yell')
    def _yell_logger(self, *events):
        for ev in events:
            self.r3.append(ev.value)
    
    @event.connect('first_name', 'last_name')
    def _set_full_name(self, *events):
        self.r4.append('')
        self._set_prop('full_name', self.first_name + ' ' + self.last_name)


class PersonNoDefault(event.HasEvents):
    def __init__(self):
        self.r1 = []
        super().__init__()
    
    @event.prop
    def first_name(self, v):
        return str(v)
    
    @event.connect('first_name')
    def _first_name_logger(self, *events):
        for ev in events:
            self.r1.append(ev.old_value + '-' + ev.new_value)
    
    @event.emitter
    def some_event(self, v):
        return dict(val=v)


@run_in_both(Person, "['', 'john doe', '', 'almar klein', '', 'jorik klein']")
def test_name(Person):
    name = Person()
    name._set_full_name.handle_now()
    name.r4.append(name.full_name)
    name.first_name = 'almar'
    name.last_name = 'klein'
    name._set_full_name.handle_now()
    name.r4.append(name.full_name)
    name.first_name = 'jorik'
    name._set_full_name.handle_now()
    name.r4.append(name.full_name)
    return name.r4

@run_in_both(Person, "[3, 'bar', [1, 2, 3]]")
def test_class_attributes(Person):
    name = Person()
    return name._foo, name._bar, name.spam

@run_in_both(Person, "['john-john', 'x', 'john-john', 'john-jane', 'jane-john']")
def test_name_ev(Person):
    res = []
    name = Person()
    name._first_name_logger.handle_now()
    res.extend(name.r1)
    res.append('x')
    assert name.first_name == 'john'
    
    name = Person()
    name.first_name = 'jane'
    name.first_name = 'john'
    name._first_name_logger.handle_now()
    res.extend(name.r1)
    
    return res

@run_in_both(PersonNoDefault, "['x', 'jane-jane', 'jane-john']")
def test_name_ev_nodefault(PersonNoDefault):
    res = []
    name = PersonNoDefault()
    name._first_name_logger.handle_now()
    res.extend(name.r1)
    res.append('x')
    assert name.first_name is None
    
    name = PersonNoDefault()
    name.first_name = 'jane'
    name.first_name = 'john'
    name._first_name_logger.handle_now()
    res.extend(name.r1)
    
    return res

@run_in_both(PersonNoDefault, "[7]")
def test_emitter_ev_nodefault(PersonNoDefault):
    res = []
    def handler(*events):
        for ev in events:
            res.append(ev.val)
    
    name = PersonNoDefault()
    handler = name.connect(handler, 'some_event')
    
    name.some_event(7)
    handler.handle_now()
    
    return res 


## Test prop

@run_in_both(Person, "['john-john', 'john-jane']")
def test_prop_init(Person):
    # First_name gets default value
    name = Person()
    assert name.first_name == 'john'
    assert not name.r1
    name._first_name_logger.handle_now()
    assert name.r1
    name.first_name = 'jane'
    #
    assert name.first_name == 'jane'
    name._first_name_logger.handle_now()
    return name.r1


@run_in_both(Person, "[]")
def test_prop_setting(Person):
    name = Person()
    name.first_name = 'john'
    name._first_name_logger.handle_now()
    name.r1 = []
    #
    name.first_name = 'jane'
    name._first_name_logger.handle_now()
    assert len(name.r1) == 1
    #
    name.first_name = 'jane'  # same name!
    name._first_name_logger.handle_now()
    assert len(name.r1) == 1
    return []


@run_in_both(Person, "[]")
def test_prop_fail(Person):
    # Fail in setting prop should raise
    name = Person()
    name.age = 99
    assert name.age == 99
    try:
        name.age = 'john'
    except Exception:
        return []
    return ['fail']


## Test readonly

@run_in_both(Person, "['-', '-john doe', 'john doe-jane doe']")
def test_readonly_init(Person):
    # full name gets default value
    name = Person()
    assert name.full_name == ''
    assert len(name.r2) ==0 
    name._full_name_logger.handle_now()
    assert len(name.r2) == 1
    name._set_prop('full_name', 'john doe')
    assert len(name.r2) == 1
    name._full_name_logger.handle_now()
    assert len(name.r2) == 2
    #
    name._set_prop('full_name', 'jane doe')
    name._full_name_logger.handle_now()
    return name.r2


@run_in_both(Person, "[]")
def test_readonly_setting(Person):
    name = Person()
    name._set_prop('full_name', 'john doe')
    name._full_name_logger.handle_now()
    name.r2 = []
    #
    name._set_prop('full_name', 'jane doe')
    name._full_name_logger.handle_now()
    assert len(name.r2) == 1
    #
    name._set_prop('full_name', 'jane doe')  # same name!
    name._full_name_logger.handle_now()
    assert len(name.r2) == 1
    return []


@run_in_both(Person, "[]")
def test_readonly_fail(Person):
    # Fail in setting readonly should raise
    name = Person()
    name._set_prop('nchildren', 3)
    assert name.nchildren == 3
    try:
        name.nchildren = 'john'
    except Exception:
        return []
    return ['fail']


## Test emitter

@run_in_both(Person, "[4, 4, 'ok']")
def test_emitter(Person):
    # emit
    name = Person()
    name._set_prop('nchildren', 3)
    assert len(name.r3) == 0
    name.yell(4)
    name.yell(4)
    assert len(name.r3) == 0
    name._yell_logger.handle_now()
    assert len(name.r3) == 2
    # fail in emitter
    try:
        name.yell('john')
    except Exception:
        name.r3.append('ok')
    return name.r3


## Test emiter related

@run_in_both(Person, "['setreadonly', 'setemitter', '_setprop1', '_setprop2']")
def test_try_illegal_stuff(Person):
    # we cannot test delete, because deleting *is* possible
    # on JS
    res = []
    name = Person()
    try:
        name.full_name = 'john doe'
    except AttributeError:
        res.append('setreadonly')
    try:
        name.yell = 3
    except AttributeError:
        res.append('setemitter')
    try:
        name._set_prop(3, 3)  # Property name must be a string
    except TypeError:
        res.append('_setprop1')
    try:
        name._set_prop('spam', 3)  # MyObject has not spam property
    except AttributeError:
        res.append('_setprop2')
    return res


class PropRecursion(event.HasEvents):
    count = 0
    
    @event.prop
    def foo(self, v=1):
        v = float(v)
        self.bar = v + 1
        return v
    
    @event.prop
    def bar(self, v=2):
        v = float(v)
        self.foo = v - 1
        return v
    
    @event.connect('foo', 'bar')
    def handle(self, *events):
        self.count += 1


@run_in_both(PropRecursion, "[]")
def test_prop_recursion(PropRecursion):
    
    m = PropRecursion()
    m.handle.handle_now()
    assert m.count == 1
    assert m.foo == 1
    assert m.bar== 2
    
    m.foo = 50
    m.handle.handle_now()
    assert m.count == 2
    assert m.foo == 50
    assert m.bar== 51
    
    m.bar = 50
    m.handle.handle_now()
    assert m.count == 3
    assert m.foo == 49
    assert m.bar== 50
    return []


## Test HasEvents class

@run_in_both(Person, "[3, 'bar', [1, 2, 3]]")
def test_hasevents_class_attributes(Person):
    name = Person()
    return name._foo, name._bar, name.spam


@run_in_both(Person, "['yell']")
def test_hasevents___emitters__(Person):
    name = Person()
    return name.__emitters__

@run_in_both(Person, "['age', 'first_name', 'full_name', 'last_name', 'nchildren']")
def test_hasevents___properties__(Person):
    name = Person()
    return name.__properties__

@run_in_both(Person, "['_first_name_logger', '_full_name_logger', '_set_full_name', '_yell_logger']")
def test_hasevents___handlers__(Person):
    name = Person()
    return name.__handlers__


@run_in_both(Person, "['age', 'first_name', 'full_name', 'last_name', 'nchildren', 'yell']")
def test_get_event_types(Person):
    name = Person()
    return name.get_event_types()


@run_in_both(Person, "[2, 1, 0]")
def test_get_event_handlers1(Person):
    name = Person()
    return [len(name.get_event_handlers('first_name')),
            len(name.get_event_handlers('full_name')),
            len(name.get_event_handlers('age')),
           ]

@run_in_both(Person, "[]")
def test_get_event_handlers2(Person):
    res1 = []
    res2 = []
    
    def func1(*events):
        for ev in events:
            res1.append(ev.new_value)
    def func2(*events):
        for ev in events:
            res2.append(ev.new_value)
    
    name = Person()
    handler1 = name.connect(func1, 'first_name', 'last_name')
    handler2 = name.connect(func2, 'first_name', 'last_name')
    handler3 = name.connect(lambda x:None, 'foo')
    
    first_handlers = name.get_event_handlers('first_name')
    assert handler1 in first_handlers
    assert handler2 in first_handlers
    assert handler3 not in first_handlers
    
    return []

@run_in_both(Person, "['x1-y1', 'x2-y2']")
def test_emit(Person):
    name = Person()
    name._first_name_logger.handle_now()
    name.r1 = []
    name.emit('first_name', dict(old_value='x1', new_value='y1'))
    name.emit('first_name', dict(old_value='x2', new_value='y2'))
    assert not name.r1
    name._first_name_logger.handle_now()
    return name.r1


@run_in_both(Person, "['ok-label', 'ok-type']")
def test_emit_fail(Person):
    res = []
    name = Person()
    try:
        name.emit('first_name:xx', dict(old_value='x1', new_value='y1'))
    except ValueError:
        res.append('ok-label')
    try:
        name.emit('first_name', 4)
    except TypeError:
        res.append('ok-type')
    return res


@run_in_both(Person, "[]")
def test_dispose1(Person):
    name = Person()
    name.dispose()  # in Py we test cleanup, here we only test if is callable
    return []


@run_in_both(Person, "['john', 'jane', 'johnny', 1]")
def test_connect1(Person):
    res = []
    res2 = []
    def func(*events):
        res2.append(1)
        for ev in events:
            res.append(ev.new_value)
    
    name = Person()
    handler = name.connect(func, 'first_name')
    assert handler is not func
    
    name.first_name = 'jane'
    name.first_name = 'jane'
    name.first_name = 'johnny'
    handler.handle_now()
    res.append(len(res2))
    return res


@run_in_both(Person, "['john', 'doe', 'jane', 'jansen', 'johnny', 1]")
def test_connect2(Person):
    res = []
    res2 = []
    def func(*events):
        res2.append(1)
        for ev in events:
            res.append(ev.new_value)
    
    name = Person()
    handler = name.connect(func, 'first_name', 'last_name')
    assert handler is not func
    
    name.first_name = 'jane'
    name.last_name = 'jansen'
    name.first_name = 'jane'
    name.first_name = 'johnny'
    handler.handle_now()
    res.append(len(res2))
    return res


@run_in_both(Person, "['john', 'doe', 'jane', 'jansen', 'johnny', 1]")
def test_connect3(Person):
    res = []
    res2 = []
    def func(*events):
        res2.append(1)
        for ev in events:
            res.append(ev.new_value)
    
    name = Person()
    handler = name.connect('first_name', 'last_name', func)  # func can also come last
    assert handler is not func
    
    name.first_name = 'jane'
    name.last_name = 'jansen'
    name.first_name = 'jane'
    name.first_name = 'johnny'
    handler.handle_now()
    res.append(len(res2))
    return res


@run_in_both(Person, "['john', 'doe', 'jane', 'jansen', '||'," +
                     " 'john', 'doe', 'jane', 'jansen']")
def test_disconnect_dispose(Person):
    res1 = []
    res2 = []
    
    def func1(*events):
        for ev in events:
            res1.append(ev.new_value)
    def func2(*events):
        for ev in events:
            res2.append(ev.new_value)
    
    name = Person()
    handler1 = name.connect(func1, 'first_name', 'last_name')
    handler2 = name.connect(func2, 'first_name', 'last_name')
    
    name.first_name = 'jane'
    name.last_name = 'jansen'
    name.dispose()  # disconnect handler
    name.first_name = 'xx'
    name.last_name = 'yy'
    handler1.handle_now()
    handler2.handle_now()
    return res1 + ['||'] + res2


@run_in_both(Person, "['jane', 'jansen', '||', 'jane', 'jansen']")
def test_disconnect1(Person):
    res1 = []
    res2 = []
    
    def func1(*events):
        for ev in events:
            res1.append(ev.new_value)
    def func2(*events):
        for ev in events:
            res2.append(ev.new_value)
    
    name = Person()
    handler1 = name.connect(func1, 'first_name', 'last_name')
    handler2 = name.connect(func2, 'first_name', 'last_name')
    
    # reset, since connecting generates a first event
    handler1.handle_now()
    handler2.handle_now()
    assert len(res1) == 2
    res1 = []
    res2 = []
    
    name.first_name = 'jane'
    name.last_name = 'jansen'
    name.disconnect('first_name')  # disconnect handler
    name.disconnect('last_name')  # disconnect handler
    name.first_name = 'xx'
    name.last_name = 'yy'
    handler1.handle_now()
    handler2.handle_now()
    return res1 + ['||'] + res2



@run_in_both(Person, "['jane', 'jansen', 'yy', '||', 'jane', 'jansen', 'xx']")
def test_disconnect2(Person):
    res1 = []
    res2 = []
    
    def func1(*events):
        for ev in events:
            res1.append(ev.new_value)
    def func2(*events):
        for ev in events:
            res2.append(ev.new_value)
    
    name = Person()
    handler1 = name.connect(func1, 'first_name', 'last_name')
    handler2 = name.connect(func2, 'first_name', 'last_name')
    
    # reset, since connecting generates a first event
    handler1.handle_now()
    handler2.handle_now()
    assert len(res1) == 2
    res1 = []
    res2 = []
    
    name.first_name = 'jane'
    name.last_name = 'jansen'
    name.disconnect('first_name', handler1)  # disconnect handler
    name.disconnect('last_name', handler2)  # disconnect handler
    name.first_name = 'xx'
    name.last_name = 'yy'
    handler1.handle_now()
    handler2.handle_now()
    return res1 + ['||'] + res2


@run_in_both(Person, "['jane', 'jansen', '||', 'jane', 'jansen', 'xx', 'yy']")
def test_disconnect3(Person):
    res1 = []
    res2 = []
    
    def func1(*events):
        for ev in events:
            res1.append(ev.new_value)
    def func2(*events):
        for ev in events:
            res2.append(ev.new_value)
    
    name = Person()
    handler1 = name.connect(func1, 'first_name:label1', 'last_name:label1')
    handler2 = name.connect(func2, 'first_name:label2', 'last_name:label2')
    
    # reset, since connecting generates a first event
    handler1.handle_now()
    handler2.handle_now()
    assert len(res1) == 2
    res1 = []
    res2 = []
    
    name.first_name = 'jane'
    name.last_name = 'jansen'
    name.disconnect('first_name:label1')  # disconnect handler
    name.disconnect('last_name:label1')  # disconnect handler
    name.first_name = 'xx'
    name.last_name = 'yy'
    handler1.handle_now()
    handler2.handle_now()
    return res1 + ['||'] + res2


class InheritedPerson1(PersonNoDefault):
    
    @event.prop
    def first_name(self, v='Ernie'):
        return str(v) + '.'
    
    @event.connect('first_name')
    def _first_name_logger(self, *events):
        super()._first_name_logger(*events)
        self.r1.append('X' + str(len(events)))

class InheritedPerson2(InheritedPerson1):
    
    @event.connect('first_name')
    def _first_name_logger(self, *events):
        super()._first_name_logger(*events)
        self.r1.append('Y' + str(len(events)))
    
    @event.emitter
    def some_event(self, v):
        return super().some_event(v + 1)
    
    @event.emitter
    def null_event(self):
        return None
    
    @event.emitter
    def non_null_event(self):
        return {}


@run_in_both(InheritedPerson2, "['ernie.-ernie.', 'ernie.-jane.', 'x2', 'y2', 8]")
def test_inheritance(InheritedPerson2):
    # property behavior can be overloaded, and handlers can be overloaded.
    # super can be used, and works for at least two levels
    name = InheritedPerson2()
    name.first_name = 'jane'
    name._first_name_logger.handle_now()
    
    # Test emitter inheritance
    def handler(*events):
        for ev in events:
            name.r1.append(ev.val)
    handler = name.connect(handler, 'some_event')
    #
    name.some_event(7)
    handler.handle_now()
    
    return name.r1

@run_in_both(InheritedPerson2, "['non_null_event']")
def test_emitter_return_val(InheritedPerson2):
    # property behavior can be overloaded, and handlers can be overloaded.
    # super can be used, and works for at least two levels
    name = InheritedPerson2()
    name.first_name = 'jane'
    name._first_name_logger.handle_now()
    
    # Test emitter inheritance
    def handler(*events):
        for ev in events:
            name.r1.append(ev.type)
    handler = name.connect(handler, 'null_event', 'non_null_event')
    
    name.r1 = []
    name.null_event()
    name.non_null_event()
    handler.handle_now()
    
    return name.r1


## Test handlers

@run_in_both(Person, "[]")
def test_event_object_persistence(Person):
    res1 = []
    res2 = []
    
    def func1(*events):
        for ev in events:
            res1.append(ev)
    def func2(*events):
        for ev in events:
            res2.append(ev)
    
    name = Person()
    handler1 = name.connect(func1, 'first_name', 'last_name')
    handler2 = name.connect(func2, 'first_name', 'last_name')
    
    # reset, since connecting generates a first event
    handler1.handle_now()
    handler2.handle_now()
    assert len(res1) == 2
    res1 = []
    res2 = []
    
    name.first_name = 'jane'
    name.last_name = 'jansen'
    handler1.handle_now()
    handler2.handle_now()
    
    assert len(res1) == 2
    assert len(res2) == 2
    assert res1[0] is res2[0]
    assert res1[1] is res2[1]
    return []


@run_in_both(Person, "['john', 'doe', 'jane', 'jansen', 0, 0, 4]")
def test_handler_calling(Person):
    res1 = []
    res2 = []
    
    def func1(*events):
        res2.append(len(events))
        for ev in events:
            res1.append(ev.new_value)
    
    name = Person()
    handler1 = name.connect(func1, 'first_name', 'last_name')
    
    assert len(res2) == 0
    handler1()
    assert len(res2) == 1
    func1()
    assert len(res2) == 2
    name.first_name = 'jane'
    name.last_name = 'jansen'
    assert len(res2) == 2
    handler1.handle_now()
    assert len(res2) == 3
    return res1 + res2


@run_in_both(Person, "['jane', 'jansen', '||', 'jane', 'jansen', 'zz', 'xx', 'yy']")
def test_handler_dispose(Person):
    res1 = []
    res2 = []
    
    def func1(*events):
        for ev in events:
            res1.append(ev.new_value)
    def func2(*events):
        for ev in events:
            res2.append(ev.new_value)
    
    name = Person()
    handler1 = name.connect(func1, 'first_name', 'last_name')
    handler2 = name.connect(func2, 'first_name', 'last_name')
    
    # reset, since connecting generates a first event
    handler1.handle_now()
    handler2.handle_now()
    assert len(res1) == 2
    res1 = []
    res2 = []
    
    name.first_name = 'jane'
    name.last_name = 'jansen'
    handler1.handle_now()
    handler2.handle_now()
    name.first_name = 'zz'  # event is pended, but discarted when disposed
    handler1.dispose()
    name.first_name = 'xx'
    name.last_name = 'yy'
    handler1.handle_now()
    handler2.handle_now()
    return res1 + ['||'] + res2


@run_in_both(Person, "['_first_name_logger']")
def test_handler_get_name(Person):
    res1 = []
    
    def func1(*events):
        for ev in events:
            res1.append(ev.new_value)
    
    name = Person()
    handler1 = name.connect(func1, 'first_name', 'last_name')
    
    res1.append(name._first_name_logger.get_name())
    assert handler1.get_name()  # on JS we cannot know the name
    
    return res1


@run_in_both(Person, "[['first_name', ['first_name']], ['last_name', ['last_name']]]")
def test_handler_get_connection_info(Person):
    res1 = []
    
    def func1(*events):
        for ev in events:
            res1.append(ev.new_value)
    
    name = Person()
    handler1 = name.connect(func1, 'first_name', 'last_name')
    
    info = handler1.get_connection_info()
    
    # Strip the labels, because on CI the func name becomes "anonymous"
    info[0][1][0] = info[0][1][0].split(':')[0]
    info[1][1][0] = info[1][1][0].split(':')[0]
    return info


class Simple1(event.HasEvents):
    
    def __init__(self):
        super().__init__()
        self._r1 = []
    
    @event.prop
    def val(self, v=0):
        return int(v)
    
    @event.connect('val')
    def on_val(self, *events):  # on_xx used to make implicit handler, but no more
        for ev in events:
            self._r1.append(ev.new_value)

@run_in_both(Simple1, "[0, 7, 42]")
def test_handler_on_method(Simple1):
    
    s = Simple1()
    s.val = 7
    s.val = 42
    for h in s.get_event_handlers('val'):
        h.handle_now()
    return s._r1


class Order1(event.HasEvents):
    
    def __init__(self):
        super().__init__()
        self.r = []
    
    @event.connect('foo')
    def bbb(self, *events):
        for ev in events:
            self.r.append('b')
    
    @event.connect('foo')
    def mmm(self, *events):
        for ev in events:
            self.r.append('m')
    
    @event.connect('foo:aaa')
    def ppp(self, *events):
        for ev in events:
            self.r.append('p')
    
    @event.connect('foo:ddd')
    def www(self, *events):
        for ev in events:
            self.r.append('w')

@run_in_both(Order1, "['m', 'p', 'b', 'w']")
def test_event_order1(Order1):
    # Hah! we determine order simply by using handle_now()
    m = Order1()
    m.emit('foo', {})
    
    m.mmm.handle_now()
    m.ppp.handle_now()
    m.bbb.handle_now()
    m.www.handle_now()
    
    return m.r


@run_in_both(Order1, "['p', 'b', 'w', 'm']")
def test_event_order2(Order1):
    
    # monkey patch JS event system
    if this_is_js():
        pending_funcs = []
        def setTimeout(func):
            pending_funcs.append(func)
        root.setTimeout = setTimeout
    
    m = Order1()
    m.emit('foo', {})
    
    if this_is_js():
        for func in pending_funcs:
            func()
    else:
        event.loop.iter()
    
    return m.r


@run_in_both(Order1, "['p', 'b', 'c', 'w', 'm']")
def test_event_order3(Order1):
    
    # monkey patch JS event system
    if this_is_js():
        pending_funcs = []
        def setTimeout(func):
            pending_funcs.append(func)
        root.setTimeout = setTimeout
    
    m = Order1()
    def myfunc(*events):
        for ev in events:
            m.r.append('c')
    m.connect(myfunc, 'foo:ccc')
    m.emit('foo', {})
    
    if this_is_js():
        for func in pending_funcs:
            func()
    else:
        event.loop.iter()
    
    return m.r


if not os.getenv('TRAVIS'):
    # Meeh, specific version of Node?
    
    @run_in_both(Order1, "['p', 'b', 'c', 'w', 'm']")
    def test_event_order4(Order1):
        
        # monkey patch JS event system
        if this_is_js():
            pending_funcs = []
            def setTimeout(func):
                pending_funcs.append(func)
            root.setTimeout = setTimeout
        
        m = Order1()
        def ccc(*events):
            for ev in events:
                m.r.append('c')
        m.connect(ccc, 'foo')  # use name of function
        m.emit('foo', {})
        
        if this_is_js():
            for func in pending_funcs:
                func()
        else:
            event.loop.iter()
        
        return m.r


class ConnectFail(event.HasEvents):
    
    @event.connect('foo.bar')
    def failing_handler(self, *events):
        pass

@run_in_both(ConnectFail, "['ok']")
def test_handler_connection_fail1(ConnectFail):
    
    try:
        m = ConnectFail()
    except RuntimeError:
        return ['ok']
    return ['fail']


@run_in_both(Person, "['ok']")
def test_handler_connection_fail2(Person):
    
    name = Person()
    def handler(*events):
        pass
    
    try:
        name.connect(handler, 'foo.bar')
    except RuntimeError:
        return ['ok']
    return ['fail']


class HandlerFail(event.HasEvents):
    
    @event.prop
    def foo(self, v=0):
        return int(v)
        
    @event.connect('foo')
    def failing_handler(self, *events):
        raise IndexError('bla')


@run_in_both(HandlerFail, "', 1, 1]")
def test_handler_exception1(HandlerFail):
    res = []
    
    m = HandlerFail()
    def handler(*events):
        raise IndexError('bla')
    handler = m.connect(handler, 'foo')
    
    # Does not fail when triggered
    m.foo = 3
    m.foo = 42
    m.failing_handler.handle_now()
    handler.handle_now()
    
    # But calling directly fails
    try:
        m.failing_handler()
    except IndexError:
        res.append(1)
    try:
        handler()
    except IndexError:
        res.append(1)
    
    return ["!!!!"] + res  # trick to ditch stderr in JS


## Dynamism

class Node(event.HasEvents):
    
    def __init__(self):
        super().__init__()
        self._r1 = []
        self._r2 = []
    
    @event.prop
    def val(self, v=0):
        return int(v)
    
    @event.prop
    def parent(self, v=None):
        return v
    
    @event.prop
    def children(self, v=()):
        return tuple(v)
    
    @event.connect('parent.val')
    def handle_parent_val(self, *events):
        for ev in events:
            if self.parent:
                self._r1.append(self.parent.val)
            else:
                self._r1.append(None)
    
    @event.connect('children*.val')
    def handle_children_val(self, *events):
        for ev in events:
            if isinstance(ev.new_value, (int, float)):
                self._r2.append(ev.new_value)
            else:
                self._r2.append('null')


@run_in_both(Node, "[17, 18, 29]")
def test_dynamism1(Node):
    n = Node()
    n1 = Node()
    n2 = Node()
    
    loop.iter()
    
    n.parent = n1
    n.val = 42
    loop.iter()
    n1.val = 17
    n2.val = 27
    loop.iter()
    n1.val = 18
    n2.val = 28
    loop.iter()
    n.parent = n2
    loop.iter()
    n1.val = 19
    n2.val = 29
    loop.iter()
    n.parent = None
    loop.iter()
    n1.val = 11
    n2.val = 21
    loop.iter()
    return n._r1


@run_in_both(Node, "[17, 18, 29]")
def test_dynamism2a(Node):
    n = Node()
    n1 = Node()
    n2 = Node()
    
    res = []
    
    def func(*events):
        for ev in events:
            if n.parent:
                res.append(n.parent.val)
            else:
                res.append(None)
    handler = n.connect(func, 'parent.val')
    
    loop.iter()
    
    n.parent = n1
    n.val = 42
    handler.handle_now()
    n1.val = 17
    n2.val = 27
    handler.handle_now()
    n1.val = 18
    n2.val = 28
    handler.handle_now()
    n.parent = n2
    handler.handle_now()
    n1.val = 19
    n2.val = 29
    handler.handle_now()
    n.parent = None
    handler.handle_now()
    n1.val = 11
    n2.val = 21
    handler.handle_now()
    return res


@run_in_both(Node, "[null, null, 17, 18, null, 29, null]")
def test_dynamism2b(Node):
    n = Node()
    n1 = Node()
    n2 = Node()
    
    res = []
    
    def func(*events):
        for ev in events:
            if ev.type == 'val':
                res.append(n.parent.val)
            else:
                res.append(None)
    handler = n.connect(func, 'parent', 'parent.val')  # also connect to parent
    
    loop.iter()
    
    n.parent = n1
    n.val = 42
    handler.handle_now()
    n1.val = 17
    n2.val = 27
    handler.handle_now()
    n1.val = 18
    n2.val = 28
    handler.handle_now()
    n.parent = n2
    handler.handle_now()
    n1.val = 19
    n2.val = 29
    handler.handle_now()
    n.parent = None
    handler.handle_now()
    n1.val = 11
    n2.val = 21
    handler.handle_now()
    return res


@run_in_both(Node, "[17, 27, 18, 28, 29]")
def test_dynamism3(Node):
    n = Node()
    n1 = Node()
    n2 = Node()
    
    loop.iter()
    
    n.children = n1, n2
    n.val = 42
    n.handle_children_val.handle_now()
    n1.val = 17
    n2.val = 27
    n.handle_children_val.handle_now()
    n1.val = 18
    n2.val = 28
    n.handle_children_val.handle_now()
    n.children = (n2, )
    n.handle_children_val.handle_now()
    n1.val = 19
    n2.val = 29
    n.handle_children_val.handle_now()
    n.children = ()
    n.handle_children_val.handle_now()
    n1.val = 11
    n2.val = 21
    n.handle_children_val.handle_now()
    return n._r2


@run_in_both(Node, "[17, 27, 18, 28, 29]")
def test_dynamism4a(Node):
    n = Node()
    n1 = Node()
    n2 = Node()
    
    res = []
    
    def func(*events):
        for ev in events:
            if isinstance(ev.new_value, (float, int)):
                res.append(ev.new_value)
            else:
                res.append('null')
    handler = n.connect(func, 'children*.val')
    
    loop.iter()
    
    n.children = n1, n2
    n.val = 42
    handler.handle_now()
    n1.val = 17
    n2.val = 27
    handler.handle_now()
    n1.val = 18
    n2.val = 28
    handler.handle_now()
    n.children = (n2, )
    handler.handle_now()
    n1.val = 19
    n2.val = 29
    handler.handle_now()
    n.children = ()
    handler.handle_now()
    n1.val = 11
    n2.val = 21
    handler.handle_now()
    return res


@run_in_both(Node, "['null', 'null', 17, 27, 18, 28, 'null', 29, 'null']")
def test_dynamism4b(Node):
    n = Node()
    n1 = Node()
    n2 = Node()
    
    res = []
    
    def func(*events):
        for ev in events:
            if isinstance(ev.new_value, (float, int)):
                res.append(ev.new_value)
            else:
                res.append('null')
    handler = n.connect(func, 'children', 'children*.val')  # also connect children
    
    loop.iter()
    
    n.children = n1, n2
    n.val = 42
    handler.handle_now()
    n1.val = 17
    n2.val = 27
    handler.handle_now()
    n1.val = 18
    n2.val = 28
    handler.handle_now()
    n.children = (n2, )
    handler.handle_now()
    n1.val = 19
    n2.val = 29
    handler.handle_now()
    n.children = ()
    handler.handle_now()
    n1.val = 11
    n2.val = 21
    handler.handle_now()
    return res


@run_in_both(Node, "[0, 17, 18, 19]")
def test_dynamism5(Node):
    # connection strings with static attributes - no reconnect
    n = Node()
    n1 = Node()
    n.foo = n1
    
    res = []
    def func(*events):
        for ev in events:
            if isinstance(ev.new_value, (float, int)):
                res.append(ev.new_value)
            else:
                res.append('null')
    handler = n.connect(func, 'foo.val')
    
    loop.iter()
    
    n.val = 42
    handler.handle_now()
    n1.val = 17
    n1.val = 18
    handler.handle_now()
    n.foo = None  # no reconnect in this case
    handler.handle_now()
    n1.val = 19
    handler.handle_now()
    return res


@run_in_both(Node, "[7, 8, 17]")
def test_deep1(Node):
    # deep connectors
    
    n = Node()
    n1 = Node()
    n2 = Node()
    n.children = Node(), n1
    n.children[0].children = Node(), n2
    
    loop.iter()
    
    res = []
    def func(*events):
        for ev in events:
            if isinstance(ev.new_value, (float, int)):
                if ev.new_value:
                    res.append(ev.new_value)
            else:
                res.append('null')
    handler = n.connect(func, 'children**.val')
    
    loop.iter()
    
    # We want these
    n1.val = 7
    handler.handle_now()
    n2.val = 8
    handler.handle_now()
    # But not these
    n.val = 42
    handler.handle_now()
    n1.children = Node(), Node()
    n.children[0].children = []
    # again ...
    n1.val = 17
    handler.handle_now()
    n2.val = 18  # n2 is no longer in the tree
    handler.handle_now()
    return res


@run_in_both(Node, "['id12', 'id11', 'id10', 'id11']")
def test_deep2(Node):
    # deep connectors - string ends in deep connector
    
    n = Node()
    n1 = Node()
    n2 = Node()
    n.children = Node(), n1
    n.children[0].children = Node(), n2
    
    loop.iter()
    
    res = []
    def func(*events):
        for ev in events:
            if isinstance(ev.new_value, (float, int)):
                res.append(ev.new_value)
            elif ev.type == 'children':
                if ev.source.val:
                    res.append('id%i' % ev.source.val)
            else:
                res.append('null')
    handler = n.connect(func, 'children**')
    
    loop.iter()
    
    # Give val to id by - these should have no effect on res though
    n.val = 10
    handler.handle_now()
    n1.val = 11
    handler.handle_now()
    n2.val = 12
    handler.handle_now()
    # Change children
    n2.children = Node(), Node(), Node()
    n1.children = Node(), Node()
    n.children = Node(), n1, Node()
    handler.handle_now()
    n2.children = []  # no longer in the tree
    n1.children = []
    handler.handle_now()
    
    return res


run_tests_if_main()
