"""
Example to mix BoxPanel and VBox, which at some point failed in Chrome. Now
Flexx takes precautions to make it work. This example is to test that it
still works.
"""

from flexx import app, ui


class Red(ui.Widget):
    CSS = '.flx-Red { background: #ff0000;}'


class Deep2(ui.Widget):

    def init(self):

        with ui.VBox():

            ui.Label(text='Widgets in BoxPanels in a widget in a vbox')

            with ui.Widget(flex=1):
                with ui.VFix():
                    with ui.HFix():
                        Red(flex=1)
                        Red(flex=1)
                    with ui.HFix():
                        Red(flex=1)
                        Red(flex=1)


if __name__ == '__main__':
    m = app.launch(Deep2, 'app')
    app.run()
