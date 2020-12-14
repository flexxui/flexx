"""
Simple example of TabLayout
"""

from flexx import app, ui, flx


class Example(ui.Widget):

    def init(self):
        with ui.TabLayout() as self.t:
            self.a = ui.MultiLineEdit(title='input', style='background:#a00;')
            self.b = ui.Widget(title='green', style='background:#0a0;')
            self.c = ui.Widget(title='blue', style='background:#00a;')


if __name__ == '__main__':
     m = flx.launch(Example, 'default-browser')
     flx.run()
