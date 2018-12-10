from flexx.util.testing import run_tests_if_main, raises
from flexx.util.logging import capture_log

import time
import asyncio
import threading
import multiprocessing

from flexx import app, event


def test_add_handlers():
    server = app.current_server()
    tornado_app = server.app
    assert tornado_app.add_handlers


def test_restarting():
    """ Test stopping and starting the ioloop.
    """
    res = []
    def add_res(i):
        res.append(i)

    def try_start():
        try:
            app.start()
        except RuntimeError:
            res.append('RTE')

    # Create new ioloop always
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    # Make Flexx use it
    server = app.create_server()

    loop.call_soon(add_res, 1)
    loop.call_soon(add_res, 2)
    loop.call_soon(app.stop)  # actually, just calling stop() would work as well
    app.start()
    assert server._running == False

    loop.call_soon(try_start)  # test that cannot start twice
    loop.call_soon(add_res, 3)
    loop.call_soon(add_res, 4)
    loop.call_soon(app.stop)
    app.start()
    assert server._running == False

    loop.call_soon(try_start)  # test that cannot start twice
    loop.call_soon(add_res, 5)
    loop.call_soon(add_res, 6)
    loop.call_soon(app.stop)
    app.start()
    assert server._running == False

    assert res == [1, 2, 'RTE', 3, 4, 'RTE', 5, 6]


def test_more_stopping():
    """ Test calling stop multiple times.
    """

    # This is why you want to create new IOLoop instances for each test

    # Create new ioloop and make Flexx use it
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    server = app.create_server()

    app.stop()  # triggers event to stop
    app.start()

    app.stop()  # Extra stop - pending stop event

    # Which means the next stop does hardly block
    t0 = time.time()
    loop.call_later(0.2, app.stop)
    app.start()
    assert time.time() - t0 < 0.1


    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    server = app.create_server()

    # But stops dont stack
    app.stop()
    app.stop()
    app.stop()
    app.stop()

    # Flush all stops ...
    app.stop()
    app.start()

    # ... so that we now have an expected loop
    t0 = time.time()
    loop.call_later(0.2, app.stop)
    app.start()
    assert time.time() - t0 >= 0.1


def test_rebinding_ioloop():
    """ Test recreating server objects, and its binding to the current ioloop.
    """

    res = []
    def add_res(i):
        res.append(i)

    # Create new ioloop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Create new flexx server, which binds to that loop
    server1 = app.create_server()
    assert server1 is app.current_server()
    #
    assert loop is server1._loop

    # Create new ioloop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # This is a new loop
    assert loop is not server1._loop

    # Create new flexx server, which binds to that loop
    server2 = app.create_server()
    assert server2 is app.current_server()
    assert server1 is not server2
    #
    assert loop is server2._loop


def test_flexx_in_thread1():
    """ Test threading and ioloop selection.
    """

    def main():
        asyncio.set_event_loop(loop2)
        app.create_server()

    # Create 3 loops, nr 2 is made current in the thread
    loop1 = asyncio.new_event_loop()
    loop2 = asyncio.new_event_loop()
    loop3 = asyncio.new_event_loop()

    asyncio.set_event_loop(loop1)
    server1 = app.create_server()

    t = threading.Thread(target=main)
    t.start()
    t.join()
    server2 = app.current_server()  # still current as set by the thread

    asyncio.set_event_loop(loop3)
    server3 = app.create_server()

    assert server1._loop is loop1
    assert server2._loop is loop2
    assert server3._loop is loop3


def test_flexx_in_thread2():
    """ Test running a component in another thread.
    """
    res = []

    class MyComponent1(event.Component):
        foo = event.IntProp(0, settable=True)

        @event.reaction('foo')
        def on_foo(self, *events):
            for ev in events:
                res.append(ev.new_value)

    def main():
        # Create fresh ioloop and make flexx use it
        # event.loop.reset()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        app.create_server()
        # Create component and manipulate prop
        comp = MyComponent1()
        comp.set_foo(3)
        comp.set_foo(4)
        # Run mainloop for one iterartion
        loop.call_later(0.2, app.stop)
        app.start()

    t = threading.Thread(target=main)
    event.loop.reset()
    t.start()
    t.join()
    event.loop.integrate()

    assert res == [0, 3, 4]


def test_flexx_in_thread3():
    """ Test starting and creating server when a server is currently running.
    """
    res = []

    def main():
        # Create fresh ioloop and make flexx use it
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        app.create_server()  # calls event.loop.integrate()
        app.start()

    def try_start():
        try:
            app.start()
        except RuntimeError:
            res.append('start-fail')

    def try_create():
        try:
            main()
        except RuntimeError:
            res.append('create-fail')  # because create_server() cannot close current

    t = threading.Thread(target=main)
    t.start()

    # With that thread running ...
    while not app.current_server()._running:
        time.sleep(0.01)

    with raises(RuntimeError):
        app.start()

    with raises(RuntimeError):
        app.create_server()

    t1 = threading.Thread(target=try_start)
    t1.start()
    t1.join()

    t2 = threading.Thread(target=try_create)
    t2.start()
    t2.join()

    # Stop
    app.stop()  # Start does not work, but we can stop it!
    t.join()  # Otherwise it would never join
    # Note that we cannot start it right after calling stop, because it wont
    # stop *at once*. We need to join first.

    assert res == ['start-fail', 'create-fail']


def test_flexx_in_thread4():
    """ Test threading starting server in other thread where it is created.
    """
    res = []

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    app.create_server()

    def try_start():
        try:
            app.stop()
            app.start()
        except RuntimeError:
            res.append('start-fail')
        else:
            res.append('start-ok')

    def main():
        app.create_server(loop=asyncio.new_event_loop())
        try_start()

    # Try to start server that was created in other thread -> fail
    t = threading.Thread(target=try_start)
    t.start()
    t.join()

    # Try to start in same thread as created -> ok
    t = threading.Thread(target=main)
    t.start()
    t.join()

    assert res == ['start-fail', 'start-ok']


def test_flexx_in_thread5():
    """ Test using loop arg for easier use.
    """
    res = []

    server = app.create_server(loop=asyncio.new_event_loop())
    assert server.serving
    # note: mmmm, I don't particularly like this, but need it to get Tornado working
    assert server._loop is asyncio.get_event_loop()

    def main():
        # likewise, we cannot do this atm
        # app.stop()
        # app.start()
        try:
            curloop = asyncio.get_event_loop()
        except RuntimeError:
            res.append(4)
        else:
            assert server._loop is curloop
            res.append(3)

    t = threading.Thread(target=main)
    t.start()
    t.join()

    assert res == [4]


def multiprocessing_func():
    import flexx
    app.create_server(port=0)  # Explicitly ask for unused port
    app.call_later(0.1, app.stop)
    app.start()


def test_flexx_multiprocessing():
    """ Using multiprocessing, multiple Flexx event loops can run in parallel.
    """
    # Can't do this with threading, because Flexx uses a global server

    t0 = time.time()

    processes = []
    for i in range(10):
        p = multiprocessing.Process(target=multiprocessing_func)
        p.daemon = True
        p.start()
        processes.append(p)

    for p in processes:
        p.join()

    # time to start processes is unpredictable, especially on pypy
    t1 = time.time()
    # assert t1 - t0 < len(processes) * 0.1

    assert True  # Just arriving here is enough to pass this test


def test_serving_apps_at_output_message():
    """ Test for 'Serving apps at' ready signal.
    """
    with capture_log('info') as log:
        server = app.create_server()
        app.stop()  # triggers event to stop
        app.start()

    assert 'Serving apps at' in ''.join(log)

run_tests_if_main()
