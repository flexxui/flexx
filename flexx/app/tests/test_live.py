""" Test components live.
"""

import os
import sys
import time
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
        where = 'File "%s", line %i, in %s' % (func.__code__.co_filename,
                                               func.__code__.co_firstlineno,
                                               func.__name__)
        smart_compare('rp', pyref, pyresult, 'Python on\n  ' + where)
        smart_compare('rj', jsref, jsresult, 'JavaScript on\n  ' + where)
        
    return runner

##


class PyComponentA(app.PyComponent):
    
    foo = event.IntProp(settable=True)
    sub = event.ComponentProp(settable=True)
    
    @event.action
    def greet(self, msg):
        print('hi', msg)


class JsComponentA(app.JsComponent):
    
    foo = event.IntProp(settable=True)
    sub = event.ComponentProp(settable=True)
    
    @event.action
    def greet(self, msg):
        print('hi', msg)


## PyComponent basics

@run_live
async def test_pycomponent_action():
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
async def test_pycomponent_prop():
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
    


##


@run_live
async def test_jscomponent_simple():
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


## Pycomponent in JsComponent

# 
# c0 = PyComponentA()
# assert c0._sessions == []
# 
# # c1, s1 = launch(JsComponentA, c0)
# c2, s2 = launch(JsComponentA, sub=c0)
# c3, s3 = launch(JsComponentA)
# c3.set_sub(c0)
# 
# 
# assert c0._sessions == [s2, s3]
# 




## Instanbtiate JsComponent

# Cannot just instantiate JsComponent
# d = JsComponentA()



##

# test_pycomponent_action()
test_pycomponent_prop()
# test_jscomponent_simple()
test_jscomponent_prop()
# run_tests_if_main()
 