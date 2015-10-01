"""
Example of object that allows the user to get/set temperature in both
Celcius and Fahrenheit. Inspired by an example from the Trellis project.
"""

from flexx import react


class Temperature(react.HasSignals):
    
    @react.input('F')
    def C(v=32, f=None):
        if f is None:
            return float(v)
        else:
            return (f - 32)/1.8
    
    @react.input('C')
    def F(v=0, c=None):
        if c is None:
            return float(v)
        else:
            return c * 1.8 + 32
            
    
    @react.connect('C')
    def show(self, c):
        print('  degrees Celcius: %1.2f' % self.C())
        print('  degrees Fahrenheit: %1.2f' % self.F())


print('Init:')
t = Temperature()

print('Water if freezing:')
t.C(0)

print('Average annual temp in California')
t.F(59.4)
