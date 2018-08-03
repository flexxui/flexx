# doc-export: Main
"""
Simple hello world following the recommended style of writing apps,
using a custom widget that is populated in its ``init()``.
"""


from flexx import flx

class Main(flx.Widget):

    def init(self):
        self.b1 = flx.Button(text='Hello')
        self.b2 = flx.Button(text='World')

if __name__ == '__main__':
    m = flx.launch(Main)
    flx.run()
