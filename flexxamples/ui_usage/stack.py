"""
Example of VBox, HBox and StackLayout
"""

from flexx import event, flx


class Example(flx.Widget):

    def init(self):
        with flx.VBox():
            with flx.HBox():
                self.buta = flx.Button(text='red')
                self.butb = flx.Button(text='green')
                self.butc = flx.Button(text='blue')
                flx.Widget(flex=1)  # space filler
            with flx.StackLayout(flex=1) as self.stack:
                self.buta.w = flx.Widget(style='background:#a00;')
                self.butb.w = flx.Widget(style='background:#0a0;')
                self.butc.w = flx.Widget(style='background:#00a;')

    @event.reaction('buta.pointer_down', 'butb.pointer_down', 'butc.pointer_down')
    def _stacked_current(self, *events):
        button = events[-1].source
        self.stack.set_current(button.w)


if __name__ == '__main__':
    m = flx.launch(Example, 'default-browser')
    flx.run()
