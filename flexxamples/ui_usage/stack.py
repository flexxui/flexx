"""
Example of VBox, HBox and StackLayout
"""

from flexx import app, event, ui, flx


class Example(ui.Widget):

    def init(self):
        with ui.VBox():
            with ui.HBox():
                self.buta = ui.Button(text='red')
                self.butb = ui.Button(text='green')
                self.butc = ui.Button(text='blue')
                ui.Widget(flex=1)  # space filler
            with ui.StackLayout(flex=1) as self.stack:
                self.buta.w = ui.Widget(style='background:#a00;')
                self.butb.w = ui.Widget(style='background:#0a0;')
                self.butc.w = ui.Widget(style='background:#00a;')

    @event.reaction('buta.pointer_down', 'butb.pointer_down', 'butc.pointer_down')
    def _stacked_current(self, *events):
        button = events[-1].source
        self.stack.set_current(button.w)


if __name__ == '__main__':
     m = flx.launch(Example, 'default-browser')
     flx.run()
