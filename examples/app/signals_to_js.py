"""
Example demonstrating how signals in JS can connect to signals in Py.
"""

from flexx import react
from flexx import app


class Name(app.Pair):
    
    @react.input
    def first_name(n='john'):
        return n
    
    @react.input
    def last_name(n='doe'):
        return n
    
    class JS:
        
        def _init(this):
            print('Hello from JS (here is some proof:', '2'*3, ')')
        
        @react.connect('first_name', 'last_name')
        def full_name(first, last):
            return first + ' ' + last
        
        @react.connect('full_name')
        def _show_name(n):
            print('Name:', n)


name = app.launch(Name, 'nodejs')
name.first_name('jane')
app.run()
