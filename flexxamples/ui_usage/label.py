"""
Simple use of a label
"""

from flexx import app, event, ui, flx


class Example(ui.Widget):

    def init(self):
        self.label = ui.Label(text="Number:")
        self.label = ui.Label(html="<b> 45 </b>")


if __name__ == '__main__':
     m = flx.launch(Example, 'default-browser')
     flx.run()
