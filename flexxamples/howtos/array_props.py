"""
Example demonstrating partial mutations to array properties. The example
has two components, one of which has an list property which is mutated
incrementally. The other component replicates the list. In practice, the other
component would e.g. manage elements in the DOM, or other resources.
"""

from flexx import event


class Test1(event.Component):

    data = event.ListProp([], doc='An array property')

    @event.action
    def add(self, i):
        self._mutate_data([i], 'insert', len(self.data))


class Test2(event.Component):

    other = event.ComponentProp(None, settable=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.data = []  # just a local variable, not a property

    @event.reaction('other.data')
    def track_data(self, *events):
        for ev in events:
            if ev.mutation == 'set':
                self.data[:] = ev.new_value
            elif ev.mutation == 'insert':
                self.data[ev.index:ev.index] = ev.objects
            elif ev.mutation == 'remove':
                self.data[ev.index:ev.index+ev.objects] = []  # objects is int here
            elif ev.mutation == 'replace':
                self.data[ev.index:ev.index+len(ev.objects)] = ev.objects
            else:
                raise NotImplementedError(ev.mutation)

            # The above shows all the cases that one should handle to cover
            # all possible array mutations. If you just want to keep an
            # array in sync, you can just use:
            #     event.mutate_array(self.data, ev)
            # which would work in JS and Python, on normal lists and ndarrays.


test1 = Test1()
test2 = Test2(other=test1)

test1.add(4)
test1.add(7)
test1.add(6)

print(test2.data)  # Events have not been send yet
event.loop.iter()
print(test2.data)  # Now they are
