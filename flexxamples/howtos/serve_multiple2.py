# doc-export: MultiApp
"""
Import apps from other example modules, and host these as widgets in a
single app.
"""

from flexx import flx

from flexxamples.demos.drawing import Drawing
from flexxamples.howtos.splitters import Split
from flexxamples.demos.twente import Twente


class MultiApp(flx.TabLayout):
    def init(self):
        Drawing(title='Drawing')
        Split(title='Split')
        Twente(title='Twente')


if __name__ == '__main__':
    # This example is setup as a desktop app
    flx.launch(MultiApp)
    flx.run()
