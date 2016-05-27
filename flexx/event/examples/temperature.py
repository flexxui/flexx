"""
This example demonstrates how props can set each-other without
getting into an infinite loop.
"""

from flexx import event


class Temperature(event.HasEvents):
    """ Temperature object with a settable prop for both Celcius and
    Fahrenheit.
    """
    
    @event.prop
    def C(self, t=0):
        t = float(t)
        self.F = t * 1.8 + 32
        return t
    
    @event.prop
    def F(self, t=0):
        t = float(t)
        self.C = (t - 32) / 1.8
        return t
    
    @event.connect('C', 'F')
    def on_temp_change(self, *events):
        # This gets called once with two events when either C or F is changed.
        print('  temp in Celcius: %1.1f C' % self.C)
        print('  temp in Fahrenheit: %1.1f F' % self.F)

t = Temperature()

print('Water if freezing:')
t.C = 0

print('Average annual temp in California')
t.F = 59.4

event.loop.iter()
