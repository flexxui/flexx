from flexx.util.testing import run_tests_if_main, raises

import time
import threading
import multiprocessing

from tornado.ioloop import IOLoop

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
    loop = IOLoop()
    loop.make_current()
    # Make Flexx use it
    server = app.create_server()
    
    app.call_later(0, add_res, 1)
    app.call_later(0, add_res, 2)
    app.call_later(0, app.stop)  # actually, just calling stop() would work as well
    app.start()
    assert server._running == False
    
    app.call_later(0, try_start)  # test that cannot start twice
    app.call_later(0, add_res, 3)
    app.call_later(0, add_res, 4)
    app.call_later(0, app.stop)
    app.start()
    assert server._running == False
    
    app.call_later(0, try_start)  # test that cannot start twice
    app.call_later(0, add_res, 5)
    app.call_later(0, add_res, 6)
    app.call_later(0, app.stop)
    app.start()
    assert server._running == False
    
    assert res == [1, 2, 'RTE', 3, 4, 'RTE', 5, 6]


def test_more_stopping():
    """ Test calling stop multiple times.
    """
    
    # This is why you want to create new IOLoop instances for each test
    
    # Create new ioloop and make Flexx use it
    loop = IOLoop()
    loop.make_current()
    server = app.create_server()
    
    app.stop()  # triggers event to stop
    app.start()
    
    app.stop()  # Extra stop - pending stop event
    
    # Which means the next stop does hardly block
    t0 = time.time()
    app.call_later(0.2, app.stop)
    app.start()
    assert time.time() - t0 < 0.1
    
    
    loop = IOLoop()
    loop.make_current()
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
    app.call_later(0.2, app.stop)
    app.start()
    assert time.time() - t0 >= 0.1


def test_rebinding_ioloop():
    """ Test recreating server objects, and its binding to the current ioloop.
    """
    
    res = []
    def add_res(i):
        res.append(i)
    
    # Create new ioloop
    loop = IOLoop()
    loop.make_current()
    
    # Create new flexx server, which binds to that loop
    server1 = app.create_server()
    assert server1 is app.current_server()
    #
    assert loop is server1._loop
    
    # Create new ioloop
    loop = IOLoop()
    loop.make_current()
    
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
        loop2.make_current()
        app.create_server()
    
    # Create 3 loops, nr 2 is made current in the thread
    loop1 = IOLoop()
    loop2 = IOLoop()
    loop3 = IOLoop()
    
    loop1.make_current()
    server1 = app.create_server()
    
    t = threading.Thread(target=main)
    t.start()
    t.join()
    server2 = app.current_server()  # still current as set by the thread
    
    loop3.make_current()
    server3 = app.create_server()
    
    assert server1._loop is loop1
    assert server2._loop is loop2
    assert server3._loop is loop3


def test_flexx_in_thread2():
    """ Test running a HasEvents object in another thread.
    """
    res = []
    
    class MyModel1(event.HasEvents):
        @event.prop
        def foo(self, v=0):
            return v
        
        @event.connect('foo')
        def on_foo(self, *events):
            for ev in events:
                res.append(ev.new_value)
    
    def main():
        # Create fresh ioloop and make flexx use it
        loop = IOLoop()
        loop.make_current()
        app.create_server()
        # Create model and manipulate prop
        model = MyModel1()
        model.foo = 3
        model.foo = 4
        # Run mainloop for one iterartion
        app.call_later(0, app.stop)
        app.start()

    t = threading.Thread(target=main)
    t.start()
    t.join()
    
    assert res == [0, 3, 4]


def test_flexx_in_thread3():
    """ Test starting and creating server when a server is currently running.
    """
    res = []
    
    def main():
        # Create fresh ioloop and make flexx use it
        loop = IOLoop()
        loop.make_current()
        app.create_server()
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
            res.append('create-fail')

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
    
    loop = IOLoop()
    loop.make_current()
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
        app.create_server()
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
    """ Test using new_loop for easier use.
    """
    res = []
    
    server = app.create_server(new_loop=True)
    assert server.serving
    assert server.loop is not IOLoop.current()
    
    def main():
        app.stop()
        app.start()
        assert server.loop is IOLoop.current()
        res.append(3)
    
    t = threading.Thread(target=main)
    t.start()
    t.join()
    
    assert res == [3]


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


run_tests_if_main()
