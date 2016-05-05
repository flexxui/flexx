"""
Example that demonstrates how you can write code that reacts to changes
in properties.

This example is adapted from event/react_to_props.py and reacts
to properties in JavaScript instead.
"""

from flexx import app, event


class MyModel(app.Model):
    
    @event.prop
    def foo(self, v=0):
        return float(v)
    
    class JS:
        
        @event.connect('foo')
        def react_to_foo_a(self, *events):
            for ev in events:
                print('A: foo changed from %f to %f' % (ev.old_value,
                                                        ev.new_value))
        
        @event.connect('foo')
        def react_to_foo_b(self, *events):
            print('B: foo changed from %f to %f' % (events[0].old_value, 
                                                    events[-1].new_value))

m = app.launch(MyModel, 'nodejs')

m.foo = 3
m.foo = 7

app.run()
