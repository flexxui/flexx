# doc-export: Form
"""
Simple example that shows two forms, one which is stretched, and one
in which we use a dummy Widget to fill up space so that the form is
more compact.

This example also demonstrates how CSS can be used to apply a greenish theme.
"""

from flexx import app, ui


class Form(ui.Widget):
    
    CSS = """
    .flx-Button {
        background: #9d9;
    }
    .flx-LineEdit {
        border: 2px solid #9d9;
    }
    """
    
    def init(self):
        
        with ui.HFix():
            with ui.FormLayout() as self.form:
                self.b1 = ui.LineEdit(title='Name:', text='Hola')
                self.b2 = ui.LineEdit(title='Age:', text='Hello world')
                self.b3 = ui.LineEdit(title='Favorite color:', text='Foo bar')
                ui.Button(text='Submit')
            with ui.FormLayout() as self.form:
                self.b4 = ui.LineEdit(title='Name:', text='Hola')
                self.b5 = ui.LineEdit(title='Age:', text='Hello world')
                self.b6 = ui.LineEdit(title='Favorite color:', text='Foo bar')
                ui.Button(text='Submit')
                ui.Widget(flex=1)  # Add a spacer


if __name__ == '__main__':
    m = app.launch(Form, 'app')
    app.run()
