# doc-export: LocalAssets
"""
Simple hello world app loading local assets.
"""

from flexx import flx
import os

BASE_DIR = os.getcwd()

with open(BASE_DIR + '/static/css/style.css') as f:
    style = f.read()

with open(BASE_DIR + '/static/js/script.js') as f:
    script = f.read()

flx.assets.associate_asset(__name__, 'style.css', style)
flx.assets.associate_asset(__name__, 'script.js', script)


class Main(flx.Widget):
    def init(self):
        flx.Widget(flex=1)
        with flx.VBox():
            with flx.HBox():
                self.b1 = flx.Button(text='Hello', css_class="border-red", flex=1)
                self.b2 = flx.Button(text='World', css_class="border-green", flex=1)
        flx.Widget(flex=1)


if __name__ == '__main__':
    m = flx.launch(Main)
    flx.run()
