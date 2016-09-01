"""
Same as init_order1.py, but now with a nested objects.
"""

from flexx import app, event


class SubModel(app.Model):
    
    def init(self):
        print('Py %s: in init' % self.id)
        self.spam = 5
    
    @event.prop
    def foo(self, v=2):
        print('Py %s: setting foo' % self.id)
        return v
    
    @event.connect('foo')
    def on_foo(self, *events):
        for ev in events:
            print('Py %s: handling %s event' % (self.id, ev.type),
                  self.foo + self.spam)

    class JS:
        
        def init(self):
            print('JS %s: in init' % self.id)
            self.eggs = 5
        
        @event.prop
        def bar(self, v=2):
            print('JS %s: setting bar' % self.id)
            return v
        
        @event.connect('bar')
        def on_bar(self, *events):
            for ev in events:
                print('JS %s: handling %s event' % (self.id, ev.type),
                      self.bar + self.eggs)


class MainModel(SubModel):
    
    def init(self):
        super().init()
        
        # Create submodel. All the initialization of that model occurs
        # now. What remains for the main model is connecting the
        # handlers (including possibly handlers for events on the sub
        # model) and the subsequent handling of events.
        self.sub = SubModel()

if __name__ == '__main__':
    m = app.launch(MainModel)
    app.run()
