"""
Example similar to greeter1.py, but with reactions defined outside of
the class. This style is generally not recommended.
"""

from flexx import event

class Person(event.Component):
    
    first_name = event.prop('Jane', setter=str)
    last_name = event.prop('Doe', setter=str)
    children = event.prop([], 'The children of this person')
    
    @event.action
    def add_child(self, child):
        self._set_children(self.children + [child])
    

p1 = Person()

# Actions defined outside the class

@p1.reaction('first_name', 'last_name')
def greet_explicit1(*events):
    for ev in events:
        p = ev.source
        print('Hi explicit1 %s %s' % (p.first_name, p.last_name))


def greet_explicit2(*events):
    for ev in events:
        p = ev.source
        print('Hi explicit2 %s %s' % (p.first_name, p.last_name))
p1.reaction(greet_explicit2, 'first_name', 'last_name')


p1.set_first_name('Jane')
p1.set_last_name('Jansen')

event.loop.iter()
