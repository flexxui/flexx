# doc-export: Form
"""
Simple example that shows two forms, one which is stretched, and one
in which we use a dummy Widget to fill up space so that the form is
more compact.
"""

from flexx import app, ui


class Form(ui.Widget):
    
    def init(self):
        
        with ui.BoxPanel():
            with ui.FormLayout() as self.form:
                self.b1 = ui.Button(title='Name:', text='Hola')
                self.b2 = ui.Button(title='Age:', text='Hello world')
                self.b3 = ui.Button(title='Favorite color:', text='Foo bar')
            with ui.FormLayout() as self.form:
                self.b4 = ui.Button(title='Name:', text='Hola')
                self.b5 = ui.Button(title='Age:', text='Hello world')
                self.b6 = ui.Button(title='Favorite color:', text='Foo bar')
                ui.Widget(flex=1)  # Add a flexer


if __name__ == '__main__':
    m = app.launch(Form, 'browser')
    app.run()
