# doc-export: MyApp
"""
Example that demonstrates the recommended way to handle state, especially
for larger apps. The trick is to define a single place that represents
the state of the app. Other states, like label text properties only derive
from it.

The ``root`` attribute is available from any component, in Python as well
as in JavaScript.

It may seem like the ``LineEdit`` widgets can represent the source of the
person's name, and they can for smaller apps, but the root is easier accessible,
and the ways to set the name can change without affecting the parts of your
application that react to the name properties.

"""

from flexx import flx


class MyApp(flx.JsComponent):
    """ This the root of the app, accessible via self.root on any component.
    It functions as a central data-store. In this case it is a JsComponent,
    but it can also be a PyComponent if that makes more sense.
    """

    first_name = flx.StringProp(settable=True)
    last_name = flx.StringProp(settable=True)

    def init(self):
        View()


class MyPersonLabel(flx.Widget):
    """ A simple widget that renders the name.
    """

    def _render_dom(self):
        return [self.root.first_name + ' ' + self.root.last_name]


class View(flx.Widget):
    """ This displays the person's name, as well as the input fields to update it.
    """

    def init(self):
        with flx.VBox():

            with flx.HBox():
                self.first_edit = flx.LineEdit(placeholder_text='first name',
                                              text='Jane')
                self.last_edit = flx.LineEdit(placeholder_text='last name',
                                             text='Doe')
                flx.Widget(flex=1)  # spacer

            with flx.HBox():
                flx.Label(text=lambda: self.root.first_name,
                         style='border:1px solid red')
                flx.Label(text=lambda: self.root.last_name,
                         style='border:1px solid red')
                flx.Widget(flex=1)  # spacer

            MyPersonLabel(style='border:1px solid blue')

            flx.Widget(flex=1)  # spacer

    @flx.reaction
    def _update_name(self):
        self.root.set_first_name(self.first_edit.text)
        self.root.set_last_name(self.last_edit.text)


if __name__ == '__main__':
    m = flx.launch(MyApp)
    flx.run()
