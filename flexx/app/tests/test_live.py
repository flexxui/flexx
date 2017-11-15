""" Test components live.
"""

import os
import sys
import time

import tornado

from flexx import app, event, webruntime
from flexx.pyscript import this_is_js

from flexx.util.testing import run_tests_if_main, raises, skip

from flexx.event import loop
from flexx.event._both_tester import FakeStream, smart_compare


ON_TRAVIS = os.getenv('TRAVIS', '') == 'true'
ON_PYPY = '__pypy__' in sys.builtin_module_names

TIMEOUT1 = 1.0  # Failsafe
TIMEOUT2 = 1.0


def filter_stdout(text):
    py_lines = []
    js_lines = []
    for line in text.strip().splitlines():
        if 'JS: ' in line:
            js_lines.append(line.split('JS: ', 1)[1])
        elif not line.startswith(('[I', '[D')):
            py_lines.append(line)
    return '\n'.join(py_lines), '\n'.join(js_lines)


def run_component_live(cls):
    
    def wrapper(func):
        
        def runner():
            # Run with a fresh server and loop
            loop.reset()
            server = app.create_server(port=0, new_loop=True)
            
            orig_stdout = sys.stdout
            orig_stderr = sys.stderr
            fake_stdout = FakeStream()
            sys.stdout = sys.stderr = fake_stdout
            try:
                c = app.launch(cls, 'firefox-app')
                func(c._sessions[0], c)
                
                # To exit
                isrunning = True
                def stop1():
                    c._sessions[0].call_after_roundtrip(stop2)
                def stop2():
                    if isrunning:
                        app.stop()
                app.call_later(0.1, stop1)
                
                # Enter main loop until we get out
                t0 = time.time()
                app.start()  # this blocks
                
            finally:
                sys.stdout = orig_stdout
                sys.stderr = orig_stderr
                loop.reset()
            
            # Clean up / shut down
            print('ran %f seconds' % (time.time()-t0))
            # assert not isrunning, "start() did not block, are you running Tornado interactively?"
            isrunning = False
            for session in c._sessions:
                session.close()
            
            # Get stdout
            pyresult, jsresult = filter_stdout(fake_stdout.getvalue())
            
            # Get reference text
            reference = '\n'.join(line[4:] for line in func.__doc__.splitlines())
            parts = reference.split('-'*10)
            pyref = parts[0].strip(' \n')
            jsref = parts[-1].strip(' \n-')
            
            smart_compare('rp', pyref, pyresult, func.__name__ + '() in Python')
            smart_compare('rj', jsref, jsresult, func.__name__ + '() in JavaScript')
            print(func.__name__, 'ok')
        
        return runner
    return wrapper



class PyComponentA(app.PyComponent):
    
    @event.action
    def greet(self, msg):
        print('hi', msg)


@run_component_live(PyComponentA)
def test_pycomponent_simple(session, c):
    """
    hi foo
    hi bar
    hi spam
    ----------
    """
    c.greet('foo')
    c.greet('bar')
    session.send_command('INVOKE', c._id, 'greet', ["spam"])


class JsComponentA(app.JsComponent):
    
    @event.action
    def greet(self, msg):
        print('hi', msg)


@run_component_live(JsComponentA)
def test_jscomponent_simple(session, c):
    """
    ----------
    hi foo
    hi bar
    hi spam
    """
    
    c.greet('foo')
    c.greet('bar')
    session.send_command('INVOKE', c._id, 'greet', ["spam"])


test_pycomponent_simple()
test_jscomponent_simple()
# run_tests_if_main()
