"""
Example that demonstrates three ways to react to changes in properties.

All reaction functions get called once when ``foo`` changes. In the first
reaction, we have no information other than the current value of foo.
In the other reactions we have more information about how `foo` changed.
"""

from flexx import event


class Test(event.Component):

    foo = event.IntProp(0, settable=True)

    @event.reaction
    def react_to_foo_a(self):
        print('A: foo changed to %i' % self.foo)

    @event.reaction('foo')
    def react_to_foo_b(self, *events):
        # This function
        print('B: foo changed from %i to %i' % (events[0].old_value,
                                                events[-1].new_value))

    @event.reaction('foo')
    def react_to_foo_c(self, *events):
        print('C: foo changed:')
        for ev in events:
            print('    from %i to %i' % (ev.old_value, ev.new_value))


c = Test()

c.set_foo(3)
c.set_foo(7)

event.loop.iter()
