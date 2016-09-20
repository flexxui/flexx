"""
Example demonstrating the emitting of events using the emit() method.

The "!" in the event name is to supress a warning for connecting to an
event that is not known beforehand (i.e. there is no corresponding
property or emitter).
"""

from flexx import event

class Basic(event.HasEvents):
    
    @event.connect('!foo')
    def on_foo(self, *events):
        print('foo handler called with %i events' % len(events))
    
    @event.connect('!bar')
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
