"""
Example that shows how two signals that are mutually dependent can 
be kept in sync, and to have this syncing work both in JS and Py. One
examplary use-case is the parent and children signal in flexx.ui.Widget.

Notes:
* The logic to define the relation is implemented both in Python and JS.
* The ``@app.no_sync`` decorator is used to only sync one of the signals
  to avoid a loop.
* In the signal that is synced, we should check whether the value is
  actually changed.

"""

from flexx import react, app
from flexx.react import undefined


class Foo(app.Model):
    
    @react.input
    def spam(self, v=0):
        if v == self.spam._value:
            return undefined
        print('set spam', self, v)
        self.eggs._set(v+1)
        return v
    
    @react.nosync
    @react.input
    def eggs(self, v):
        print('set eggs', self, v)
        self.spam._set(v-1)
        return v
    
    class JS:
        
        @react.connect('spam')
        def _spam_changed(v):
            print('JS detected spam changed to ', v)
        
        @react.input
        def spam(self, v):
            assert v is not undefined
            if v == self.spam._value:
                return undefined
            print('set spam', self, v)
            self.eggs._set(v+1)
            return v
        
        @react.nosync
        @react.input
        def eggs(self, v):
            assert v is not undefined
            print('set eggs', self, v)
            self.spam._set(v-1)
            return v

foo = Foo()
