""" Test disposing of app Components.
flexx/event/tests/test_disposing.py is focused on Component disposing by itself.
The tests in this module focus on app Components.
"""

import gc
import sys
import weakref
import asyncio

from pscript import this_is_js

from flexx import app, event

from flexx.util.testing import run_tests_if_main, raises, skipif, skip
from flexx.app.live_tester import run_live, roundtrip, launch

from flexx.event import loop

from flexx.app import PyComponent, JsComponent


def setup_module():
    app.manager._clear_old_pending_sessions(1)


class MyPyComponent(PyComponent):

    def _dispose(self):
        print('disposing', self.id)
        super()._dispose()


class MyJsComponent(JsComponent):

    def _dispose(self):
        print('disposing', self.id)
        super()._dispose()


def check_alive(s, id1, id2):
    print(getattr(s.get_component_instance(id1), 'id', None))
    print(getattr(s.get_component_instance(id2), 'id', None))
    s.send_command('EVAL', 'flexx.s1.instances.%s && flexx.s1.instances.%s.id || null' % (id1, id1))
    s.send_command('EVAL', 'flexx.s1.instances.%s && flexx.s1.instances.%s.id || null' % (id2, id2))


## PyComponent

@run_live
async def test_dispose_PyComponent1():
    """
    MyPyComponent_2
    MyPyComponent_3
    disposing MyPyComponent_2
    disposing MyPyComponent_3
    None
    None
    done
    ----------
    MyPyComponent_2
    MyPyComponent_3
    null
    null
    done
    """
    # Explicit call to dispose()

    # Init
    c, s = launch(PyComponent)
    with c:
        c1 = MyPyComponent()
        c2 = MyPyComponent()
    await roundtrip(s)
    c1_id, c2_id = c1.id, c2.id

    check_alive(s, c1_id, c2_id)
    await roundtrip(s)

    # Dispose
    c1.dispose()
    c2.dispose()
    await roundtrip(s)
    await roundtrip(s)

    check_alive(s, c1_id, c2_id)
    await roundtrip(s)

    # End
    print('done')
    s.send_command('EVAL', '"done"')
    await roundtrip(s)


@run_live
async def test_dispose_PyComponent2():
    """
    MyPyComponent_2
    MyPyComponent_3
    disposing MyPyComponent_2
    disposing MyPyComponent_3
    None
    None
    done
    ----------
    MyPyComponent_2
    MyPyComponent_3
    null
    null
    done
    """
    # Dispose by losing the reference

    # Init
    c, s = launch(PyComponent)
    with c:
        c1 = MyPyComponent()
        c2 = MyPyComponent()
    c1_id, c2_id = c1.id, c2.id
    await roundtrip(s)

    check_alive(s, c1_id, c2_id)
    await roundtrip(s)

    # Dispose via Python gc
    del c1, c2
    gc.collect()  # will schedule call to _dispose
    await roundtrip(s)  # which we will handle here

    check_alive(s, c1_id, c2_id)
    await roundtrip(s)

    # End
    print('done')
    s.send_command('EVAL', '"done"')
    await roundtrip(s)


@skipif('__pypy__' in sys.builtin_module_names, reason='pypy gc works different')
@run_live
async def test_dispose_PyComponent3():
    """
    done
    disposing MyPyComponent_2
    disposing MyPyComponent_3
    ----------
    ? Cannot dispose a PyComponent from JS
    ? Cannot dispose a PyComponent from JS
    done
    """
    # Cannot dispose from JS

    # Init
    c, s = launch(PyComponent)
    with c:
        c1 = MyPyComponent()
        c2 = MyPyComponent()
    c1_id, c2_id = c1.id, c2.id
    await roundtrip(s)

    # Try to dispose
    s.send_command('INVOKE', c1.id, 'dispose', [])
    s.send_command('INVOKE', c2.id, 'dispose', [])
    await roundtrip(s)

    # End
    print('done')
    s.send_command('EVAL', '"done"')
    await roundtrip(s)


## JsComponent


@run_live
async def test_dispose_JsComponent1():
    """
    MyJsComponent_2
    MyJsComponent_3
    None
    None
    done
    ----------
    MyJsComponent_2
    MyJsComponent_3
    disposing MyJsComponent_2
    disposing MyJsComponent_3
    null
    null
    done
    """
    # Explicit call to dispose() in Python

    # Init
    c, s = launch(PyComponent)
    with c:
        c1 = MyJsComponent()
        c2 = MyJsComponent()
    c1_id, c2_id = c1.id, c2.id
    await roundtrip(s)

    check_alive(s, c1_id, c2_id)
    await roundtrip(s)

    # Dispose from Python - also disposes in JS
    c1.dispose()
    c2.dispose()
    await roundtrip(s)

    check_alive(s, c1_id, c2_id)
    await roundtrip(s)

    # End
    print('done')
    s.send_command('EVAL', '"done"')
    await roundtrip(s)


@run_live
async def test_dispose_JsComponent2():
    """
    MyJsComponent_2
    MyJsComponent_3
    None
    None
    done
    ----------
    MyJsComponent_2
    MyJsComponent_3
    MyJsComponent_2
    MyJsComponent_3
    done
    """
    # Dispose by losing the reference

    # Init
    c, s = launch(PyComponent)
    with c:
        c1 = MyJsComponent()
        c2 = MyJsComponent()
    c1_id, c2_id = c1.id, c2.id
    await roundtrip(s)

    check_alive(s, c1_id, c2_id)
    await roundtrip(s)

    # Lose reference in Python, keeps the JS local component alive
    del c1, c2
    gc.collect()  # will schedule call to _dispose
    await roundtrip(s)  # which we will handle here

    check_alive(s, c1_id, c2_id)
    await roundtrip(s)

    # End
    print('done')
    s.send_command('EVAL', '"done"')
    await roundtrip(s)


@run_live
async def test_dispose_JsComponent3():
    """
    MyJsComponent_2
    MyJsComponent_3
    None
    None
    done
    ----------
    MyJsComponent_2
    MyJsComponent_3
    disposing MyJsComponent_2
    disposing MyJsComponent_3
    null
    null
    done
    """
    # Dispose from JS

    # Init
    c, s = launch(PyComponent)
    with c:
        c1 = MyJsComponent()
        c2 = MyJsComponent()
    c1_id, c2_id = c1.id, c2.id
    await roundtrip(s)

    check_alive(s, c1_id, c2_id)
    await roundtrip(s)

    # Dispose from JS
    s.send_command('INVOKE', c1.id, 'dispose', [])
    s.send_command('INVOKE', c2.id, 'dispose', [])
    await roundtrip(s)

    check_alive(s, c1_id, c2_id)
    await roundtrip(s)

    # End
    print('done')
    s.send_command('EVAL', '"done"')
    await roundtrip(s)


run_tests_if_main()
