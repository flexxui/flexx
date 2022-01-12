"""
Simple use of a label
"""

from flexx import flx


class Example(flx.Widget):

    def init(self):
        self.label = flx.Label(text="Number:")
        self.label = flx.Label(html="<b> 45 </b>")


if __name__ == '__main__':
    m = flx.launch(Example, 'default-browser')
    flx.run()
