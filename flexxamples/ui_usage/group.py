"""
Simple use of a group containing a few widgets
"""

from flexx import app, event, ui, flx


class Example(flx.Widget):

    def init(self):
        with ui.GroupWidget(title='A silly panel'):
            with ui.VBox():
                self.progress = ui.ProgressBar(min=0, max=9,
                                               text='Clicked {value} times')
                self.but = ui.Button(text='click me')

    @event.reaction('but.pointer_down')
    def _button_pressed(self, *events):
        self.progress.set_value(self.progress.value + 1)

        
if __name__ == '__main__':
    m = flx.launch(Example)
    flx.run()
