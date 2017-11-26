""" Test components live.
"""

import gc
import os
import sys
import time
import weakref
import asyncio

import tornado

from flexx import app, event, webruntime
from flexx.pyscript import this_is_js

from flexx.util.testing import run_tests_if_main, raises, skip

from flexx.event import loop
from flexx.event._both_tester import FakeStream, smart_compare

ON_TRAVIS = os.getenv('TRAVIS', '') == 'true'
ON_PYPY = '__pypy__' in sys.builtin_module_names


async def roundtrip(*sessions):
    """ Coroutine to await a roundtrip to all given sessions.
    """
    ok = []
    def up():
        ok.append(1)
    for session in sessions:
        session.call_after_roundtrip(up)
    # timeout = time.time() + 5.0
    while len(ok) < len(sessions):
        await asyncio.sleep(0.02)
    loop.iter()


def launch(cls, *args, **kwargs):
    """ Shorthand for app.launch() that also returns session.
    """
    c = app.App(cls, *args, **kwargs).launch('firefox-app')
    return c, c._session


def filter_stdout(text):
    py_lines = []
    js_lines = []
    for line in text.strip().splitlines():
        if 'JS: ' in line:
            js_lines.append(line.split('JS: ', 1)[1])
        elif not line.startswith(('[I', '[D')):
            py_lines.append(line)
    return '\n'.join(py_lines), '\n'.join(js_lines)


def run_live(func):
    
    def runner():
        # Run with a fresh server and loop
        loop.reset()
        #asyncio_loop = asyncio.get_event_loop()
        asyncio_loop = asyncio.new_event_loop()
        server = app.create_server(port=0, loop=asyncio_loop)
        
        print('running', func.__name__, '...', end='')
        orig_stdout = sys.stdout
        orig_stderr = sys.stderr
        fake_stdout = FakeStream()
        sys.stdout = sys.stderr = fake_stdout
        t0 = time.time()
        try:
            # Call function - it could be a co-routine
            cr = func()
            if asyncio.iscoroutine(cr):
                asyncio_loop.run_until_complete(cr)
        finally:
            sys.stdout = orig_stdout
            sys.stderr = orig_stderr
        
        # Clean up / shut down
        print('done in %f seconds' % (time.time()-t0))
        for appname in app.manager.get_app_names():
            if 'default' not in appname:
                sessions = app.manager.get_connections(appname)
                for session in sessions:
                    if session.app is not None:
                        session.app.dispose()
                        session.close()
        loop.reset()
        
        # Get reference text
        pyresult, jsresult = filter_stdout(fake_stdout.getvalue())
        reference = '\n'.join(line[4:] for line in func.__doc__.splitlines())
        parts = reference.split('-'*10)
        pyref = parts[0].strip(' \n')
        jsref = parts[-1].strip(' \n-')
        
        # Compare
        smart_compare(func, ('Python', pyresult, pyref),
                            ('JavaScript', jsresult, jsref))
    
    return runner

##


class PyComponentA(app.PyComponent):
    
    foo = event.IntProp(settable=True)
    sub = event.ComponentProp(settable=True)
    
    @event.action
    def greet(self, msg):
        print('hi', msg)
    
    @event.reaction
    def _on_foo(self):
        if self.sub is not None:
            print('sub foo changed', self.sub.foo)


class JsComponentA(app.JsComponent):
    
    foo = event.IntProp(settable=True)
    sub = event.ComponentProp(settable=True)
    
    @event.action
    def greet(self, msg):
        print('hi', msg)
    
    @event.reaction
    def _on_foo(self):
        if self.sub is not None:
            print('sub foo changed', self.sub.foo)


## PyComponent basics

@run_live
async def test_pycomponent_action1():
    """
    hi foo
    hi bar
    hi spam
    ----------
    """
    c, s = launch(PyComponentA)
    
    c.greet('foo')
    c.greet('bar')
    s.send_command('INVOKE', c._id, 'greet', ["spam"])
    await roundtrip(s)


@run_live
async def test_pycomponent_action2():
    """
    hi foo
    hi bar
    hi spam
    ----------
    """
    c1, s = launch(PyComponentA)
    
    with c1:
        c = PyComponentA()
    assert c._session is s
    
    
    c.greet('foo')
    c.greet('bar')
    s.send_command('INVOKE', c._id, 'greet', ["spam"])
    await roundtrip(s)


@run_live
async def test_pycomponent_prop1():
    """
    0
    3
    3
    ----------
    0
    3
    """
    c, s = launch(PyComponentA)
    
    c.set_foo(3)
    print(c.foo)
    s.send_command('EVAL', c._id, 'foo')
    loop.iter()
    print(c.foo)  # this will mutate foo
    await roundtrip(s)
    print(c.foo)
    s.send_command('EVAL', c._id, 'foo')
    await roundtrip(s)


@run_live
async def test_pycomponent_reaction1():
    """
    0
    sub foo changed 0
    0
    sub foo changed 3
    3
    ----------
    """
    c1, s = launch(PyComponentA)
    
    with c1:
        c2 = PyComponentA()  # PyComponent sub
    c1.set_sub(c2)
    
    print(c2.foo)
    loop.iter()
    
    c2.set_foo(3)
    
    print(c2.foo)
    loop.iter()
    print(c2.foo)
    
    await roundtrip(s)


@run_live
async def test_pycomponent_reaction2():
    """
    0
    sub foo changed 0
    0
    sub foo changed 3
    3
    ----------
    """
    c1, s = launch(PyComponentA)
    
    with c1:
        c2 = JsComponentA()  # JsComponent sub
    c1.set_sub(c2)
    
    print(c2.foo)
    await roundtrip(s)
    
    c2.set_foo(3)
    
    print(c2.foo)
    await roundtrip(s)
    print(c2.foo)
    
    await roundtrip(s)


@run_live
async def test_pycomponent_sub_pycomp1():
    """
    0
    3
    3
    ----------
    0
    3
    """
    c, s = launch(PyComponentA)
    
    # with c1:
    
    c.set_foo(3)
    print(c.foo)
    s.send_command('EVAL', c._id, 'foo')
    loop.iter()
    print(c.foo)  # this will mutate foo
    await roundtrip(s)
    print(c.foo)
    s.send_command('EVAL', c._id, 'foo')
    await roundtrip(s)

## JsComponent basics


@run_live
async def test_jscomponent_action1():
    """
    ----------
    hi foo
    hi bar
    hi spam
    """
    c, s = launch(JsComponentA)
    
    c.greet('foo')
    c.greet('bar')
    s.send_command('INVOKE', c._id, 'greet', ["spam"])
    await roundtrip(s)
    await roundtrip(s)


@run_live
async def test_jscomponent_action2():
    """
    ----------
    hi foo
    hi bar
    hi spam
    """
    c1, s = launch(JsComponentA)
    
    with c1:
        c = JsComponentA()
    assert c._session is s
    
    c.greet('foo')
    c.greet('bar')
    s.send_command('INVOKE', c._id, 'greet', ["spam"])
    await roundtrip(s)
    await roundtrip(s)


@run_live
async def test_jscomponent_prop():
    """
    0
    0
    3
    ----------
    0
    3
    """
    c, s = launch(JsComponentA)
    
    c.set_foo(3)
    print(c.foo)
    s.send_command('EVAL', c._id, 'foo')
    loop.iter()
    print(c.foo)  # still not set
    await roundtrip(s)
    print(c.foo)
    s.send_command('EVAL', c._id, 'foo')
    await roundtrip(s)


@run_live
async def test_jscomponent_reaction1():
    """
    0
    0
    3
    ----------
    sub foo changed 0
    sub foo changed 3
    """
    c1, s = launch(JsComponentA)
    
    with c1:
        c2 = PyComponentA()  # PyComponent sub
    c1.set_sub(c2)
    
    print(c2.foo)
    await roundtrip(s)
    
    c2.set_foo(3)
    
    print(c2.foo)
    await roundtrip(s)
    print(c2.foo)
    
    await roundtrip(s)

@run_live
async def test_jscomponent_reaction2():
    """
    0
    0
    3
    ----------
    sub foo changed 0
    sub foo changed 3
    """
    c1, s = launch(JsComponentA)
    
    with c1:
        c2 = JsComponentA()  # JsComponent sub
    c1.set_sub(c2)
    
    print(c2.foo)
    await roundtrip(s)
    
    c2.set_foo(3)
    
    print(c2.foo)
    await roundtrip(s)
    print(c2.foo)
    
    await roundtrip(s)


## Pycomponent in JsComponent


class CreatingPyComponent(PyComponentA):
    
    def init(self):
        self._x = JsComponentA()
    
    @event.action
    def apply_sub(self):
        self.set_sub(self._x)


class CreatingJsComponent(JsComponentA):
    
    def init(self):
        self._x = JsComponentA()
    
    @event.action
    def apply_sub(self):
        self.set_sub(self._x)


@run_live
async def test_proxy_binding1():
    """
    sub foo changed 0
    sub foo changed 0
    ----------
    """
    # Get ref to JsComponent instantiated by a PyComponent
    
    c1, s = launch(app.PyComponent)
    
    with c1:
        c2 = CreatingPyComponent()  # PyComponent that has local JsComponent
    
    await roundtrip(s)
    assert c2.sub is None
    
    # Get access to the sub component
    c2.apply_sub()
    await roundtrip(s)
    
    c3 = c2.sub
    assert isinstance(c3, JsComponentA)
    
    # Get id of c3 and get rid of any references
    c3_id = c3._id
    c3_ref = weakref.ref(c3)
    c2.set_sub(None)
    for i in range(5):
        await roundtrip(s)
    del c3
    for i in range(5):
        await roundtrip(s)
    
    assert c3_ref() is not None  # because PyComponent has it
    
    # Get access to the sub component again (proxy thereof, really)
    c2.apply_sub()
    await roundtrip(s)
    c3 = c2.sub
    assert isinstance(c3, JsComponentA)
    assert c3._id == c3_id


@run_live
async def test_proxy_binding2():
    """
    ----------
    sub foo changed 0
    sub foo changed 0
    """
    # Get ref to JsComponent instantiated by a JsComponent,
    # drop that ref, re-get the proxy instance, and verify that its
    # a different instance representing the same object in JS
    
    c1, s = launch(app.PyComponent)
    
    with c1:
        c2 = CreatingJsComponent()  # JsComponent that has local JsComponent
    
    await roundtrip(s)
    assert c2.sub is None
    
    # Get access to the sub component
    c2.apply_sub()
    await roundtrip(s)
    await roundtrip(s)
    
    c3 = c2.sub
    assert isinstance(c3, JsComponentA)
    
    # Get id of c3 and get rid of any references
    id3 = id(c3)
    c3_ref = weakref.ref(c3)
    c3_id = c3._id
    c2.set_sub(None)
    for i in range(5):  # need a few roundtrips for session to drop c3
        await roundtrip(s)
    del c3
    for i in range(5):
        await roundtrip(s)
        gc.collect()
    
    assert c3_ref() is None  # Python dropped it, but JS still has the object!
    
    # Get access to the sub component again (proxy thereof, really)
    c2.apply_sub()
    await roundtrip(s)
    c3 = c2.sub
    assert isinstance(c3, JsComponentA)
    assert c3._id == c3_id


@run_live
async def test_proxy_binding3():
    """
    sub foo changed 0
    sub foo changed 3
    sub foo changed 6
    sub foo changed 7
    ? Using stub component
    ? does not exist in this session
    ----------
    """
    # Test that local components only send events when there is a proxy,
    # and that when events are send anyway, warnings are shown
    
    c1, s = launch(PyComponentA)
    
    with c1:
        c2 = JsComponentA()  # JsComponent that has local JsComponent
    c1.set_sub(c2)
    id2 = c2._id
    
    # Change foo of c2
    c2.set_foo(3)
    await roundtrip(s)
    
    # Now, we're pretend that to drop the instance
    s.send_command('INVOKE', c2._id, '_set_has_proxy', [False])
    await roundtrip(s)
    
    # We don't get the events anymore
    c2.set_foo(4)
    c2.set_foo(5)
    await roundtrip(s)
    
    # Re-establish
    s.send_command('INVOKE', c2._id, '_set_has_proxy', [True])
    await roundtrip(s)
    
    # We get these
    c2.set_foo(6)
    s.send_command('INVOKE', id2, 'set_foo', [7])  # same thing, really
    await roundtrip(s)
    
    # Now, we simulate destroying the proxy without JS knowing
    s._component_instances.pop(id2)
    
    # And then ... invoking an event will raise one error for not being able
    # to invoke in Python, and one for not being able to decode the "source"
    # of the event.
    s.send_command('INVOKE', id2, 'set_foo', [9])
    await roundtrip(s)


class JsComponentB(app.JsComponent):
    
    sub1 = event.ComponentProp(settable=True)
    sub2 = event.ComponentProp(settable=True)
    
    @event.action
    def sub1_to_sub2(self):
        self.set_sub2(self.sub1)


@run_live
async def test_proxy_binding21():
    """
    14 None
    24 None
    24 24
    ----------
    14
    ? JsComponentA
    undefined
    ? JsComponentA
    undefined
    """
    # Test multiple sessions, and sharing objects
    
    c2, s2 = launch(JsComponentB)
    c1, s1 = launch(JsComponentB)
    
    with c1:
        c11 = JsComponentA()  # JsComponent that has local JsComponent
        c1.set_sub1(c11)
    
    with c2:
        c22 = JsComponentA()  # JsComponent that has local JsComponent
        c2.set_sub1(c22)
    await roundtrip(s1, s2)
    
    c11.set_foo(14)
    c22.set_foo(24)
    await roundtrip(s1, s2)
    
    print(c1.sub1 and c1.sub1.foo, c1.sub2 and c1.sub2.foo)
    s1.send_command('EVAL', c1._id, 'sub1.foo')
    await roundtrip(s1, s2)
    
    # So far, not much news, now break the universe ...
    
    c1.set_sub1(c2.sub1)
    await roundtrip(s1, s2)
    print(c1.sub1 and c1.sub1.foo, c1.sub2 and c1.sub2.foo)
    
    # In JS, c1.sub1 will be a stub
    s1.send_command('EVAL', c1._id, 'sub1._id')
    s1.send_command('EVAL', c1._id, 'sub1.foo')
    await roundtrip(s1, s2)
    
    # But we can still "handle" it
    c1.sub1_to_sub2()
    await roundtrip(s1, s2)
    
    # And now c1.sub2.foo has the value of c2.sub1.foo
    print(c1.sub1 and c1.sub1.foo, c1.sub2 and c1.sub2.foo)
    s1.send_command('EVAL', c1._id, 'sub1._id')
    s1.send_command('EVAL', c1._id, 'sub1.foo')
    await roundtrip(s1, s2)


## Instanbtiate JsComponent

# Cannot just instantiate JsComponent
# d = JsComponentA()

# todo: init_args is JsComponent


##

run_tests_if_main()
 