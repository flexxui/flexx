"""
Simple example of TabLayout
"""

from flexx import flx


class Example(flx.Widget):

    def init(self):
        with flx.TabLayout() as self.t:
            self.a = flx.MultiLineEdit(title='input', style='background:#a00;')
            self.b = flx.Widget(title='green', style='background:#0a0;')
            self.c = flx.Widget(title='blue', style='background:#00a;')


if __name__ == '__main__':
    m = flx.launch(Example, 'default-browser')
    flx.run()
