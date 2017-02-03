"""
App that can be used to generate errors on the Python and JS side. These
errors should show tracebacks in the correct manner (and not crash the app
as in #164).

To test thoroughly, you should probably also set the foo and bar
properties from the Python and JS console.
"""

from flexx import app, event, ui


class Errors(ui.Widget):
    
    def init(self):
        
        with ui.VBox():
            self.b1 = ui.Button(text='Raise error in JS property setter')
            self.b2 = ui.Button(text='Raise error in JS event handler')
            self.b3 = ui.Button(text='Raise error in Python property setter')
            self.b4 = ui.Button(text='Raise error in Python event handler')
            ui.Widget(flex=1)  # spacer
    
    class Both:
        
        @event.prop
        def foo(self, v=1):
            return self.reciprocal(v)
        
        def reciprocal(self, v):
            return 1 / v
        
        def raise_error(self):
            raise RuntimeError('Deliberate error')
    
    class JS:
        
        @event.prop
        def bar(self, v):
            self.raise_error()
        
        # Handlers for four buttons
        
        @event.connect('b1.mouse_click')
        def error_in_JS_prop(self, *events):
            self.bar = 2
        
        @event.connect('b2.mouse_click')
        def error_in_JS_handler(self, *events):
            self.raise_error()
        
        @event.connect('b3.mouse_click')
        def error_in_Py_prop(self, *events):
            self.foo = 0
    
    @event.connect('b4.mouse_click')
    def error_in_Py_handler(self, *events):
        self.raise_error()


if __name__ == '__main__':
    m = app.launch(Errors, 'browser')
    app.run()
