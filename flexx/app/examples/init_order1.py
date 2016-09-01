"""
This example demonstrates the order of initialization:

* Initial property values are set.
* The init() method gets called.
* Events are handled.
"""

from flexx import app, event


class Example(app.Model):
    
    def init(self):
        print('Py: in init')
        self.spam = 5
    
    @event.prop
    def foo(self, v=2):
        print('Py: setting foo')
        return v
    
    @event.connect('foo')
    def on_foo(self, *events):
        for ev in events:
            print('Py: handling %s event' % ev.type, self.foo + self.spam)

    class JS:
        
        def init(self):
            print('JS: in init')
            self.eggs = 5
        
        @event.prop
        def bar(self, v=2):
            print('JS: setting bar')
            return v
        
        @event.connect('bar')
        def on_bar(self, *events):
            for ev in events:
                print('JS: handling %s event' % ev.type, self.bar + self.eggs)


if __name__ == '__main__':
    m = app.launch(Example)
    app.run()
