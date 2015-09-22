"""
Example that shows how two signals that are mutually dependent can 
be kept in sync, and to have this syncing work both in JS and Py. One
examplary use-case is the parent and children signal in flexx.ui.Widget.
"""

from flexx import react, app
from flexx.react import undefined


class Foo(app.Pair):
    
    @react.input
    def spam(self, v=0):
        if v == self.spam._value:
            return undefined
        print('set spam', self, v)
        self.eggs._set(v+1)
        return v
    
    @react.input
    def eggs(self, v):
        if v == self.eggs._value:
            return undefined
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
        
        @react.input
        def eggs(self, v):
            assert v is not undefined
            if v == self.eggs._value:
                return undefined
            print('set eggs', self, v)
            self.spam._set(v-1)
            return v

foo = Foo()

##
class Temperature3(react.HasSignals):
    
    @react.input
    def c(self, v=0):
        self.f(v+32)
        return v
    
    @react.input
    def f(self, v):
        self.c(v-32)
        return v

t = Temperature3()

