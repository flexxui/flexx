"""
Example that demonstrates/tests how objects survive synchronisation
jitter even if Python and JS are busy. We tried hard to make this
as painless as possible in Flexx, which is why this example may look
a bit dull. But the fact that this works is not trivial :)

What happens is that the ``the_thing`` property is set in the
``init()``. This will sync to JS, and then back again to Py (syncing
always ends at the Python side, for eventual synchronicity). However,
in the mean time, Python has set the property again, so by the time
that the prop gets synced back to Python, the first Thing is not there
anymore, and would be deleted (if we had not taken measures to prevent
that), which would cause problems.
"""

import time
from flexx import app, event, ui


class Thing(app.Model):
    
    @event.prop
    def value(self, v):
        return v


class Example(ui.Widget):
    
    def init(self):
        self.the_thing = Thing(value=2)
    
    @event.prop
    def foo(self, v=0):
        print('in foo setter')
        return v

    @event.connect('the_thing')
    def on_the_thing(self, *events):
        for ev in events:
            print('the thing became %s with value %s' % 
                  (ev.new_value.id, ev.new_value.value))

    @event.connect('foo')
    def on_foo(self, *events):
        print('sleep in Py')
        time.sleep(10)
        print('Done sleeping in Py')
            
    class Both:
        
        @event.prop
        def the_thing(self, v):
            assert isinstance(v, Thing)
            return v
   
    class JS:
        
        def init(self):
            print('sleep in JS')
            self.sleep(10)
            print('Done sleeping in JS')
        
        def sleep(self, t):
            import time
            etime = time.time() + t
            while time.time() < etime:
                pass


m = app.launch(Example)
with m:
    m.the_thing = Thing(value=3)

print('starting event loop')
app.run()
