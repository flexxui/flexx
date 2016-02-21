from flexx import event
# from flexx import react
# from flexx import watch
# from flexx import behold
# from flexx import observe

# todo: some form of propagation

class MyObject(event.EventEmitter):
    
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

@event.connect('h.foo:crap')
def handle_foo(*events):
    print('single func, handle foo', [ev.label for ev in events])

@event.connect('h.bar')
def handle_bar(*events):
    print('keep track of bar', events)

with event.loop:
    h.emit('foo', dict(msg='he'))
    h.emit('foo', dict(msg='ho'))


## Two properties that depend on each-other

class Temperature(event.EventEmitter):
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


class CachingExample(event.EventEmitter):
    """ Demonstrate the use of caching, an example use of tha analog
    of "streams" in reactive programming. We use an "undocumented"
    signal to make calculate_results push out its result. Which is
    perfectly ok for internal use.
    """
    
    def __init__(self):
        super().__init__()
    
    @event.prop
    def input(self, v=0):
        return float(v)
    
    @event.connect('input')
    def calculate_results(self, *events):
        # This takes a while
        import time
        time.sleep(self.input)
        if self.input > 0:
            self.emit('result', dict(result=42*self.input))
    
    @event.connect('result')
    def show_result(self, *events):
        print('The result is', events[-1].result)

c = CachingExample()
event.loop.iter()

# with event.loop: c.input = 3
