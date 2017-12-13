# doc-export: Split
"""
Splitter widgets are cool!
"""

from flexx import app, ui


class Split(app.PyComponent):

    def init(self):

        with ui.HSplit():
            ui.Widget(style='background:#f00')
            with ui.VSplit():
                ui.Widget(style='background:#0f0')
                with ui.HSplit():
                    ui.Widget(style='background:#ff0')
                    with ui.VSplit():
                        ui.Widget(style='background:#f0f')
                        with ui.HSplit():
                            ui.Widget(style='background:#0ff')
                            ui.Widget(style='background:#00f')


if __name__ == '__main__':
    m = app.launch(Split)
    app.run()
