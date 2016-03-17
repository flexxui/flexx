"""
Example of object that allows the user to get/set temperature in both
Celcius and Fahrenheit. Inspired by an example from the Trellis project.

Setting depending signals in the input function is probably the easiest
way to implement mutually dependent signals. See temperature2.py for
another approach.
"""

from flexx import react


class Temperature(react.HasSignals):
    
    @react.input
    def C(self, v=0):
        self.F(v*1.8+32)
        return v
    
    @react.input
    def F(self, v):
        self.C((v-32)/1.8)
        return v
    
    @react.connect('C')
    def show_c(self, c):
        print('  degrees Celcius: %1.2f' % c)
    
    @react.connect('F')
    def show_f(self, f):
        print('  degrees Fahrenheit: %1.2f' %f)


print('Init:')
t = Temperature()

print('Water if freezing:')
t.C(0)

print('Average annual temp in California')
t.F(59.4)
