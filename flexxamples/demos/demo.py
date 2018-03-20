# doc-export: Demo
"""
A demo with few lines of code with some fancy widgets, which works
as an exported app, so it can be embedded e.g. on the main page.
"""

from flexx import app, ui
from flexx.ui.examples.splines import Splines
from flexx.ui.examples.twente import Twente
from flexx.ui.examples.drawing import Drawing

class Demo(ui.Widget):
    
    def init(self):
        with ui.TabLayout():
            Splines(title='Spline demo')
            Twente(title='Temperature vis')
            Drawing(title='Drawing app')
            ui.YoutubeWidget(title='Video')


if __name__ == '__main__':
    m = app.App(Demo, title='Flexx demo').launch()
    app.run()
