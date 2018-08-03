"""
This just tests some assumptioms that we make about asyncio. These are
mostly documented, but still good to see in action.
"""

import asyncio
import threading


##

def append_current_loop(container, make_new_loop=False):
    if make_new_loop:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    try:
        container.append(asyncio.get_event_loop())
    except Exception as err:
        container.append(str(err))


def test_asyncio_thread1():
    # Tests that asyncio.get_event_loop() returns a different loop instance
    # for each thread.

    r = []
    r.append(asyncio.get_event_loop())

    t = threading.Thread(target=append_current_loop, args=(r, False))
    t.start()
    t.join()

    t = threading.Thread(target=append_current_loop, args=(r, True))
    t.start()
    t.join()

    r.append(asyncio.get_event_loop())

    assert len(r) == 4
    assert isinstance(r[1], str) and 'no current event loop in thread' in r[1]
    assert r[0] is not r[2]
    assert r[0] is r[3]

    return r


##


def make_new_loop_and_run():
    loop = asyncio.new_event_loop()
    loop.call_later(0.2, lambda: print('greeting 1 from thread', threading.current_thread().getName()))
    loop.call_later(0.7, lambda: print('greeting 2 from thread', threading.current_thread().getName()))
    loop.call_later(0.9, loop.stop)
    loop.run_forever()


def test_asyncio_thread2():
    # Run multiple loops in multiple threads at the same time.

    loop = asyncio.get_event_loop()
    assert not loop.is_running()

    tt = []
    for i in range(5):
        t = threading.Thread(target=make_new_loop_and_run)
        tt.append(t)
    for t in tt:
        t.start()
    make_new_loop_and_run()
    for t in tt:
        t.join()


if __name__ == '__main__':
    r = test_asyncio_thread1()
