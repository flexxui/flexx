# doc-export: Icons

"""
This example demonstrates the use of icons in Flexx.
"""

import os

import flexx
from flexx import app, ui

# todo: support icons in widgets like Button, TabWidget, etc.
# todo: support fontawesome icons


class Icons(ui.Widget):
    
    def init(self):
        
        ui.Button(text='Not much to see here yet')


if __name__ == '__main__':
    
    fname = os.path.join(os.path.dirname(flexx.__file__), 'resources', 'flexx.ico')
    black_png = ('iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAIUlEQVR42mNgY'
                 'GD4TyEeTAacOHGCKDxqwKgBtDVgaGYmAD/v6XAYiQl7AAAAAElFTkSuQmCC')
    
    # Select application icon. Can be a url, a relative url to a shared asset,
    # a base64 encoded image, or a local filename. Note that the local filename
    # works for setting the aplication icon in a desktop-like app, but not for
    # a web app. File types can be ico or png.
    
    icon = None  # use default
    # icon = 'https://assets-cdn.github.com/favicon.ico'
    # icon = app.assets.add_shared_asset('ico.icon', open(fname, 'rb'))
    # icon = 'data:image/png;base64,' + black_png
    # icon = fname
    
    m = app.App(Icons, title='Icon demo', icon=icon).launch('app')
    app.start()
