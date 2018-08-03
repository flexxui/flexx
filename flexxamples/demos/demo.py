# doc-export: Demo
"""
A demo with few lines of code with some fancy widgets, which works
as an exported app, so it can be embedded e.g. on the main page.
"""

from flexx import flx
from flexxamples.demos.splines import Splines
from flexxamples.demos.twente import Twente
from flexxamples.demos.drawing import Drawing

class Demo(flx.Widget):

    def init(self):
        with flx.TabLayout():
            Splines(title='Spline demo')
            Twente(title='Temperature vis')
            Drawing(title='Drawing app')
            flx.YoutubeWidget(title='Video')


if __name__ == '__main__':
    a = flx.App(Demo, title='Flexx demo')
    m = a.launch()
    flx.run()
