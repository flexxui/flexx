"""
Logic to run live tests.
"""

import gc
import sys
import time
import asyncio

from flexx.event import loop
from flexx import app

from flexx.event.both_tester import FakeStream, smart_compare


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
    # from flexx import app
    c = app.App(cls, *args, **kwargs).launch('firefox-app')
    return c, c.session


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
    """ Decorator to run a live test.
    """

    def runner():
        # Run with a fresh server and loop
        loop.reset()
        #asyncio_loop = asyncio.get_event_loop()
        asyncio_loop = asyncio.new_event_loop()
        app.create_server(port=0, loop=asyncio_loop)

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
            gc.collect()
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
