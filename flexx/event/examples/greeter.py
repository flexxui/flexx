"""
This example implements a simple class to hold a persons name, and three
ways to connect a function that will be print a greet when the name is
changed.
"""

from flexx import event

class Name(event.HasEvents):
    
    @event.prop
    def first_name(self, n='John'):
        return str(n)
    
    @event.prop
    def last_name(self, n='Doe'):
        return str(n)
    
    @event.connect('first_name', 'last_name')
    def greet1(self, *events):
        print('Hello %s %s' % (self.first_name, self.last_name))


name = Name()

# Connect a function using a decorator
@name.connect('first_name', 'last_name')
def greet2(*events):
    print('Hi %s %s' % (name.first_name, name.last_name))

# Connect a function using the classic approach
def greet3(*events):
    print('Heya %s %s' % (name.first_name, name.last_name))
name.connect(greet3, 'first_name', 'last_name')


name.first_name = 'Jane'

event.loop.iter()
