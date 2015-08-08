"""
Simple example for a person object.
"""

from flexx import react

class Person(react.HasSignals):
    
    @react.input
    def first_name(n):
        return str(n)
    
    @react.input
    def last_name(n):
        return str(n)
    
    @react.connect('first_name', 'last_name')
    def full_name(first, last):
        return first + ' ' + last
    
    @react.connect('full_name')
    def greet(n):
        print('Hello %s!' % n)

p = Person(first_name='John', last_name='Doe')
p.first_name('Jane')
