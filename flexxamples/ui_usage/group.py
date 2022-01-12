"""
Simple use of a group containing a few widgets
"""

from flexx import flx


class Example(flx.Widget):

    def init(self):
        with flx.GroupWidget(title='A silly panel'):
            with flx.VBox():
                self.progress = flx.ProgressBar(min=0, max=9,
                                               text='Clicked {value} times')
                self.but = flx.Button(text='click me')

    @flx.reaction('but.pointer_down')
    def _button_pressed(self, *events):
        self.progress.set_value(self.progress.value + 1)


if __name__ == '__main__':
    m = flx.launch(Example)
    flx.run()
