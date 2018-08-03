"""
App that can be used to generate errors on the Python and JS side. These
errors should show tracebacks in the correct manner (and not crash the app
as in #164).
"""

from flexx import app, event, ui


class ErrorsPy(app.PyComponent):

    def init(self):
        self.js = ErrorsJS(self)

    @event.action
    def do_something_stupid(self):
        self.raise_error()

    def raise_error(self):
        raise RuntimeError('Deliberate error')

    @event.reaction('!js.b4_pointer_click')
    def error_in_Py_reaction(self, *events):
        self.raise_error()


class ErrorsJS(ui.Widget):

    def init(self, pycomponent):
        self.py = pycomponent

        with ui.VBox():
            self.b1 = ui.Button(text='Raise error in JS action')
            self.b2 = ui.Button(text='Raise error in JS reaction')
            self.b3 = ui.Button(text='Raise error in Python action')
            self.b4 = ui.Button(text='Raise error in Python reaction')
            ui.Widget(flex=1)  # spacer

    @event.action
    def do_something_stupid(self):
        self.raise_error(0)

    def raise_error(self):
        raise RuntimeError('Deliberate error')

    # Handlers for four buttons

    @event.reaction('b1.pointer_click')
    def error_in_JS_action(self, *events):
        self.do_something_stupid()

    @event.reaction('b2.pointer_click')
    def error_in_JS_reaction(self, *events):
        self.raise_error()

    @event.reaction('b3.pointer_click')
    def error_in_Py_action(self, *events):
        self.py.do_something_stupid()

    @event.reaction('b4.pointer_click')
    def error_in_Py_reaction(self, *events):
        self.emit('b4_pointer_click')


if __name__ == '__main__':
    m = app.launch(ErrorsPy, 'browser')
    app.run()
