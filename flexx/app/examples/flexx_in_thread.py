"""
Example showing running Flexx' event loop in another thread.
This is not a recommended use in general.

Most parts of Flexx are not thread-save. E.g. setting properties
should generally only be done from a single thread. Event handlers
are *always* called from the same thread that runs the event loop
(unless manually called).

The app.create_server() is used to (re)create the server object, binding
it to the ioloop of the current thread. Note that app.start() must be
called from that same thread.

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

def main():
    app.create_server()
    model.foo = 2  # Probably a bad idea to set props from both threads
    app.start()

# Start Flexx server in new thread
t = threading.Thread(target=main)
t.start()

# Manipulate model from main thread (the model's on_foo() gets called from other thread)
for i in range(5, 9):
    time.sleep(1)
    model.foo = i

# Stop event loop (this is thread-safe) and wait for thread to end
app.stop()
t.join()
