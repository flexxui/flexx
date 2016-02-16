from flexx import event
# from flexx import react
# from flexx import watch
# from flexx import behold
# from flexx import observe

# todo: some form of propagation
# todo: event order
# todo: caching (streams)

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

@event.connect('h.foo')
def handle_foo(*events):
    print('single func, handle foo', [ev.msg for ev in events])

@event.connect('h.bar')
def handle_bar(*events):
    print('keep track of bar', events)

with event.loop:
    h.emit('foo', dict(msg='he'))
    h.emit('foo', dict(msg='ho'))


##

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
    
    @event.connect('C', 'F')
    def on_temp_change(self, *events):
        # This gets called once with two events when either C or F is changed.
        print('temp changed!', events)

t = Temperature2()

with event.loop:
    t.C = 10
        
