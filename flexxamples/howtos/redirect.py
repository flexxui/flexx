# doc-export: Redirect
"""
Example that demonstrates redirecting and opening a new page.
This example only works when opened in a browser (not with
``launch(Redirect, 'app')``).

Note that one can also open a webpage from Python:

import webbrowser
webbrowser.open('http://python.org')
"""

from flexx import flx


class Redirect(flx.Widget):
    
    def init(self):
        self.but1 = flx.Button(text='Redirect')
        self.but2 = flx.Button(text='Open new page')
    
    @flx.reaction('but1.pointer_click')
    def on_redirect(self, *events):
        global window
        window.location.href = 'http://python.org'  # allow going back
        # window.location.replace('http://python.org')  # hard redirect
    
    @flx.reaction('but2.pointer_click')
    def on_opennew(self, *events):
        global window
        window.open('http://python.org', '_blank')


if __name__ == '__main__':
    m = flx.launch(Redirect, 'browser')
    flx.start()
