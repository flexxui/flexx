# doc-export: Deep
"""
Example that shows deep nesting of layouts. This also functions as a
test that such deep layouts actually work.
"""

from flexx import app, ui

class Red(ui.Widget):
    CSS = '.flx-Red { background: #ff0000;}'


class Deep1(ui.Widget):
    # This was broken on Chrome earlier

    def init(self):

        with ui.VBox():

            ui.Label(text='Widget in a vbox in a widget in a vbox')

            with ui.VBox(flex=1):
                with ui.Widget(flex=1):
                    with ui.VBox():
                        ui.Label(text='---')
                        Red(flex=1)


class Deep2(ui.Widget):

    def init(self):

        with ui.VBox():

            ui.Label(text='Widget in a vbox in a vbox in a vbox')

            with ui.VBox(flex=1):

                with ui.VBox(flex=1):
                    ui.Label(text='---')
                    Red(flex=1)


class Deep3(ui.Widget):

    def init(self):

        with ui.VBox():

            ui.Label(text='Widget in a vbox in a hbox in a vbox')

            with ui.HBox(flex=1):
                ui.Label(text='|||')

                with ui.VBox(flex=1):
                    ui.Label(text='---')
                    Red(flex=1)


class Deep4(ui.Widget):

    def init(self):

        with ui.HBox():

            ui.Label(text='Widget in a hbox in a widget in a hbox')

            with ui.HBox(flex=1):
                with ui.Widget(flex=1):
                    with ui.HBox():
                        ui.Label(text='|||')
                        Red(flex=1)


class Deep5(ui.Widget):

    def init(self):

        with ui.HBox():

            ui.Label(text='Widget in a hbox in a hbox in a hbox')

            with ui.HBox(flex=1):

                with ui.HBox(flex=1):
                    ui.Label(text='|||')
                    Red(flex=1)


class Deep6(ui.Widget):

    def init(self):

        with ui.HBox():

            ui.Label(text='Widget in a hbox in a vbox in a hbox')

            with ui.VBox(flex=1):
                ui.Label(text='---')

                with ui.HBox(flex=1):
                    ui.Label(text='|||')
                    Red(flex=1)


class Deep(ui.Widget):
    def init(self):

        with ui.HFix():

            with ui.HFix():
                Deep1()
                Deep2()
                Deep3()

            with ui.VFix():
                Deep4()
                Deep5()
                Deep6()


if __name__ == '__main__':
    app.launch(Deep, 'app')
    app.run()
