# doc-export: Form
"""
Simple example that shows two forms, one which is stretched, and one
in which we use a dummy Widget to fill up space so that the form is
more compact.
"""

from flexx import app, ui


class Form(ui.Widget):
    
    def init(self):
        
        with ui.HFix():
            with ui.FormLayout() as self.form:
                self.b1 = ui.LineEdit(title='Name:', text='Hola')
                self.b2 = ui.LineEdit(title='Age:', text='Hello world')
                self.b3 = ui.LineEdit(title='Favorite color:', text='Foo bar')
            with ui.FormLayout() as self.form:
                self.b4 = ui.LineEdit(title='Name:', text='Hola')
                self.b5 = ui.LineEdit(title='Age:', text='Hello world')
                self.b6 = ui.LineEdit(title='Favorite color:', text='Foo bar')
                ui.Widget(flex=1)  # Add a flexer


if __name__ == '__main__':
    m = app.launch(Form, 'firefox-browser')
    app.run()
