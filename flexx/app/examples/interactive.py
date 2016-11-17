"""
Flexx can be used interactively in the IPython notebook, but also from
any IDE that supports event loop integration with Tornado (like e.g. Pyzo).

To use interactive mode, start your code with ``app.init_interactive()``
optionally passing a runtime of choice. Note that running this line
multiple times has no effect (it returns early if the default session
already exists).

Model classes that are instantiated outside of the context of another model
object will now get associated with the default session.
"""

from flexx import app, event, ui

# Safe to run this multiple times, just don't close the runtime
m = app.init_interactive()

# Define something ...

class Thing(app.Model):
    
    @event.prop
    def foo(self, v=0):
        return v
    
    class JS:
        
        @event.connect('foo')
        def on_foo(self, *events):
            ev = events[-1]
            print('foo is now ' + ev.new_value)

# Instantiate it just like that!
t = Thing()

# Or like this
b = ui.Button(text='push me')
