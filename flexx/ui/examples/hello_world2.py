# doc-export: Main
"""
Simple hello world following the recommended style of writing apps,
using a custom widget that is populated in its ``init()``.
"""


from flexx import app, ui

class Main(ui.Widget):
    
    def init(self):
        
        self.b1 = ui.Button(text='Hello')
        self.b2 = ui.Button(text='World')

if __name__ == '__main__':
    m = app.launch(Main)
    app.run()
