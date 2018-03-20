"""
Example showing running Flexx' event loop in another thread.
This is not a recommended use in general.

Invoking actions is thread-safe. Actions and reactions are always
executed in the thread that runs the event loop.

The app.create_server() is used to (re)create the server object. It is
important that the used asyncio loop is local to the thread.
"""

import time
import threading
import asyncio

from flexx import app, event


class MyComponent1(event.Component):
    
    foo = event.Property(0, settable=True)
    
    @event.reaction('foo')
    def on_foo(self, *events):
        for ev in events:
            print('foo changed to', ev.new_value)

# Create component in main thread
comp = MyComponent1()

# Start server in its own thread
def start_flexx():
    app.create_server(loop=asyncio.new_event_loop())
    app.start()

t = threading.Thread(target=start_flexx)
t.start()

# Manipulate component from main thread
# (the component's on_foo() gets called from other thread)
for i in range(5, 9):
    time.sleep(1)
    comp.set_foo(i)

# Stop event loop (this is thread-safe) and wait for thread to end
app.stop()
t.join()
