# doc-export: ThemedForm
"""
Simple example that shows two forms, one which is stretched, and one
in which we use a dummy Widget to fill up space so that the form is
more compact.

This example also demonstrates how CSS can be used to apply a greenish theme.
"""

from flexx import flx


class ThemedForm(flx.Widget):

    CSS = """
    .flx-Button {
        background: #9d9;
    }
    .flx-LineEdit {
        border: 2px solid #9d9;
    }
    """

    def init(self):

        with flx.HFix():
            with flx.FormLayout() as self.form:
                self.b1 = flx.LineEdit(title='Name:', text='Hola')
                self.b2 = flx.LineEdit(title='Age:', text='Hello world')
                self.b3 = flx.LineEdit(title='Favorite color:', text='Foo bar')
                flx.Button(text='Submit')
            with flx.FormLayout() as self.form:
                self.b4 = flx.LineEdit(title='Name:', text='Hola')
                self.b5 = flx.LineEdit(title='Age:', text='Hello world')
                self.b6 = flx.LineEdit(title='Favorite color:', text='Foo bar')
                flx.Button(text='Submit')
                flx.Widget(flex=1)  # Add a spacer


if __name__ == '__main__':
    m = flx.launch(ThemedForm, 'app')
    flx.run()
