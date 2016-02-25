from flexx import event
# from flexx import react
# from flexx import watch
# from flexx import behold
# from flexx import observe

# todo: some form of propagation
# todo: conductor prop? Or can that be a readonly?

class MyObject(event.HasEvents):
    
    @event.connect('foo')
    def _handle_foo(self, *events):
        print('_handle_foo', events)
    
    def on_foo(self, *events):
        # This should just work, as in vispy, and as in overloadable
        print('on_foo', events)
    
    @event.prop
    def bar(self, v=3):
        return float(v)
        
    @event.prop
    def prop_without_connections(self, v=3):
        return float(v)
    
    def on_bar(self, *events):
        print('on_bar', events)
    
    @event.prop
    def sub(self, ob=None):
        return ob
    
    @event.connect('sub.bar')
    def _handle_sub_bar(self, *events):
        print('sub bar', events)

h = MyObject(bar=5)
h1 = MyObject(bar=11)
h2 = MyObject(bar=12)

h.sub = h1

@h.connect('foo:crap')
def handle_foo(*events):
    print('single func, handle foo', [ev.label for ev in events])

@h.connect('bar')
def handle_bar(*events):
    print('keep track of bar', events)

with event.loop:
    h.emit('foo', dict(msg='he'))
    h.emit('foo', dict(msg='ho'))


## Readonly and emitter

from flexx import event

class Foo(event.HasEvents):
    
    @event.readonly
    def bar(self, v=42):
        return float(v)
    
    def on_bar(self, *events):
        print('bar changed!')
    
    @event.emitter
    def spam(self, x):
        return dict(value=x)
    
    def on_spam(self, *events):
        for ev in events:
            print('spam event:', ev)


foo = Foo()


## Two properties that depend on each-other

from flexx import event

class Temperature(event.HasEvents):
    """ Wow, this works even easier as it did with signals!
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
    
    @event.connect('C:c', 'F:f')
    def on_temp_change(self, *events):
        # This gets called once with two events when either C or F is changed.
        print('temp changed!', events)

t = Temperature()

with event.loop:
    t.C = 10
        

## Caching
from flexx import event

class CachingExample(event.HasEvents):
    """ Demonstrate the use of caching, an example use of tha analog
    of "streams" in reactive programming. We use a readonly property
    to cache the result. 
    """
    
    def __init__(self):
        super().__init__()
    
    @event.prop
    def input(self, v=0):
        """ The input for the calcualtions. There could be more inputs."""
        return float(v)
    
    @event.connect('input')
    def calculate_results(self, *events):
        """ A long running calculation on the input. """
        # This takes a while
        import time
        time.sleep(self.input)
        if self.input > 0:
            self._set_prop('result', self.input + 0.1)
    
    @event.readonly
    def result(self, v=None):
        """ readonly prop to cache the result. """
        return v
    
    @event.connect('result')
    def show_result(self, *events):
        """ handler to show result. Can be called at any time. """
        if self.result:
            print('The result is', self.result)

c = CachingExample()
event.loop.iter()

# with event.loop: c.input = 3
