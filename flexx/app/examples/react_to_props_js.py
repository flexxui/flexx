"""
Example that demonstrates how you can write code that reacts to changes
in properties.

This example is adapted from event/react_to_props.py and demonstrates
one class that reacts in JS to a Python-based prop, and one class
that reacts in Python to a JS-based prop.
"""

from flexx import app, event


class MyModel1(app.Model):
    # Has a prop on Py, react in JS
    
    @event.prop
    def foo(self, v=0.0):
        return float(v)
    
    class JS:
        
        @event.connect('foo')
        def react_to_foo_a(self, *events):
            for ev in events:
                print('A: foo changed from %s to %s' % (ev.old_value,
                                                        ev.new_value))
        
        @event.connect('foo')
        def react_to_foo_b(self, *events):
            print('B: foo changed from %s to %s' % (events[0].old_value, 
                                                    events[-1].new_value))


class MyModel2(app.Model):
    # Has a prop on JS, react in Py
    
    @event.connect('foo')
    def react_to_bar_a(self, *events):
        for ev in events:
            print('A: foo changed from %s to %s' % (ev.old_value,
                                                    ev.new_value))
    
    @event.connect('foo')
    def react_to_bar_b(self, *events):
        print('B: foo changed from %s to %s' % (events[0].old_value, 
                                                events[-1].new_value))
    
    class JS:
        
        @event.prop
        def foo(self, v=0.0):
            return float(v)
        

m = app.launch(MyModel1, 'browser')  # Change to MyModel2 to test reverse case

m.foo = 3
m.foo = 7

app.run()
