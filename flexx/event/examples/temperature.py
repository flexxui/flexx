"""
This example demonstrates how two mutually dependent props can be set
without getting into an infinite loop. Since flexx uses actions, this
is rather trivial. Technically, one could also react to one property
and invoke the set action of the other, but that would result in the
props being set infinitely.
"""

from flexx import event


class Temperature(event.Component):
    """ Temperature object with a settable prop for both Celcius and
    Fahrenheit.
    """
    
    c = event.prop(0)
    f = event.prop(0)
    
    @event.action
    def set_c(self, t):
        t = float(t)
        self._mutate_c(t)
        self._mutate_f(t * 1.8 + 32)
    
    @event.action
    def set_f(self, t):
        t = float(t)
        self._mutate_f(t)
        self._mutate_c((t - 32) / 1.8)
    
    @event.reaction
    def on_temp_change(self):
        # This gets called once with two events when either C or F is changed.
        print('  temp in Celcius: %1.1f C' % self.c)
        print('  temp in Fahrenheit: %1.1f F' % self.f)

t = Temperature()

print('Water is freezing:')
t.set_c(0)
event.loop.iter()

print('Average annual temp in California')
t.set_f(59.4)
event.loop.iter()
