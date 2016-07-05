"""
Example showing running Flexx' event loop in another thread.
This is not a recommended use in general.

Most parts of Flexx are not thread-save. E.g. setting properties
should generally only be done from a single thread. Event handlers
are *always* called from the same thread that runs the event loop
(unless manually called).

The app.create_server() is used to (re)create the server object. It is
important that the used IOLoop is local to the thread. This can be
accomplished by calling create_server() and start() from the same
thread, or using ``new_loop=True`` (as is done here).
"""

import time
import threading

from flexx import app, event


class MyModel1(event.HasEvents):
    @event.prop
    def foo(self, v=0):
        return v
    
    @event.connect('foo')
    def on_foo(self, *events):
        for ev in events:
            print('foo changed to', ev.new_value)

# Create model in main thread
model = MyModel1()

# Start server in its own thread
app.create_server(new_loop=True)
t = threading.Thread(target=app.start)
t.start()

# Manipulate model from main thread (the model's on_foo() gets called from other thread)
for i in range(5, 9):
    time.sleep(1)
    model.foo = i

# Stop event loop (this is thread-safe) and wait for thread to end
app.stop()
t.join()
