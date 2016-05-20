"""
Example demonstrating the emitting of events using the emit() method.
This also shows how a method prefixed with "on_" is automatically
connected to the corresponding event.
"""

from flexx import event

class Basic(event.HasEvents):
    
    def on_foo(self, *events):
        print('foo handler called with %i events' % len(events))
    
    def on_bar(self, *events):
        print('bar handler called with %i events' % len(events))

b = Basic()

# Emit dummy events
b.emit('foo', {})
b.emit('foo', {})
b.emit('bar', {})
b.emit('spam', {})  # we can emit this, but nobody's listening

# Handle events
event.loop.iter()
