from flexx.util.testing import run_tests_if_main, raises

import time
import asyncio
import threading

from flexx import event


def test_in_thread2():
    """ Test running a Component object in another thread.
    """
    res = []
    
    class MyComp1(event.Component):
        foo = event.IntProp(0, settable=True)
        
        @event.reaction('foo')
        def on_foo(self, *events):
            for ev in events:
                res.append(ev.new_value)
    
    def main():
        # Create fresh ioloop and make flexx use it
        # event.loop.reset()
        loop = asyncio.new_event_loop()
        event.loop.integrate(loop, reset=True)
        # Create model and manipulate prop
        model = MyComp1()
        model.set_foo(3)
        model.set_foo(4)
        # Run mainloop for one iterartion
        loop.call_later(0.2, loop.stop)
        loop.run_forever()

    t = threading.Thread(target=main)
    t.start()
    t.join()
    event.loop.integrate(reset=True)  # restore
    
    assert res == [0, 3, 4]


def test_in_thread3():
    """ Test hotswapping the loop to another thread.
    """
    res = []
    
    class MyComp1(event.Component):
        foo = event.IntProp(0, settable=True)
        
        @event.reaction('foo')
        def on_foo(self, *events):
            for ev in events:
                res.append(ev.new_value)
    
    def main():
        # Create fresh ioloop and make flexx use it
        # event.loop.reset()
        loop = asyncio.new_event_loop()
        event.loop.integrate(loop, reset=False)  # no reset!
        # Run mainloop for one iterartion
        loop.call_later(0.2, loop.stop)
        loop.run_forever()
    
    # Create model and manipulate prop
    event.loop.reset()
    model = MyComp1()
    model.set_foo(3)
    model.set_foo(4)
    
    t = threading.Thread(target=main)
    t.start()
    t.join()
    event.loop.integrate(reset=True)  # restore
    
    assert res == [0, 3, 4]


def test_in_thread4():
    """ Test invoking actions from another thread.
    """
    res = []
    
    class MyComp1(event.Component):
        foo = event.IntProp(0, settable=True)
        
        @event.reaction('foo')
        def on_foo(self, *events):
            for ev in events:
                res.append(ev.new_value)
    
    def main():
        # Create fresh ioloop and make flexx use it
        # event.loop.reset()
        loop = asyncio.new_event_loop()
        event.loop.integrate(loop, reset=False)  # no reset!
        # set foo
        model.set_foo(3)
        # Run mainloop for one iterartion
        loop.call_later(0.4, loop.stop)
        loop.run_forever()
    
    # Create model and manipulate prop
    event.loop.reset()
    model = MyComp1()
   
    t = threading.Thread(target=main)
    t.start()
    time.sleep(0.2)
    model.set_foo(4)  # invoke from main thread
    t.join()
    event.loop.integrate(reset=True)  # restore
    
    assert res == [0, 3, 4]


run_tests_if_main()
