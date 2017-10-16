"""
This example implements a simple class to hold a persons name, and different
ways to print a greeting in reaction to name changes. This example is best
run interactively.
"""

from flexx import event

class Person(event.Component):
    
    first_name = event.prop('Jane', setter=str)
    last_name = event.prop('Doe', setter=str)
    children = event.prop([], 'The children of this person')
    
    # Actions 
    
    @event.action
    def add_child(self, child):
        self._set_children(self.children + [child])
    
    @event.emitter
    def eat(self):
        #self.emit('eat', {'name': self.first_name})
        return {'name': self.first_name}
    
    # Reactions
    
    @event.reaction('first_name:xx', 'last_name')
    def greet_explitic(self, *events):
        print('Explicit hello %s %s' % (self.first_name, self.last_name))
    
    @event.reaction
    def greet_implicit(self):
        print('Implicit hello %s %s' % (self.first_name, self.last_name))
    
    @event.reaction('children*.first_name')
    def greetall_explicit(self, *events):
        print('Explicit hey kids ' + ', '.join(n.first_name for n in self.children) + '!')
    
    @event.reaction
    def greetall_implicit(self):
        print('Implicit hey kids ' + ', '.join(n.first_name for n in self.children) + '!')
    
    @event.reaction('!eat')
    def track_eating(self, *events):
        for ev in events:
            print(ev.name + ' is eating')


p1 = Person()
p2 = Person(first_name='Bob')
p3 = Person(first_name='Naomi')
p4 = Person(first_name='Ivo')

p1.add_child(p3)
p1.add_child(p4)

# These also work ...

# @name.reaction('first_name', 'last_name')
# def greet_explicit2(*events):
#     print('Hi %s %s' % (name.first_name, name.last_name))
# 
# # Connect a function using the classic approach
# def greet_explicit3(*events):
#     print('Heya %s %s' % (name.first_name, name.last_name))
# name.reaction(greet_explicit3, 'first_name', 'last_name')

event.loop.iter()
