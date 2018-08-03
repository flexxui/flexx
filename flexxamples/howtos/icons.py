# doc-export: Icons2

"""
This example demonstrates the use of icons in Flexx.

When run as a script, Icons1 is used, passing icon and title to the application.

In the examples section of the docs, Icons2 is used, which sets icon and title
in the init(). Click "open in new tab" to see the effect.


"""

import os

import flexx
from flexx import flx

# todo: support icons in widgets like Button, TabWidget, etc.
# todo: support fontawesome icons

fname = os.path.join(os.path.dirname(flexx.__file__), 'resources', 'flexx.ico')
black_png = ('data:image/png;base64,'
             'iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAIUlEQVR42mNgY'
             'GD4TyEeTAacOHGCKDxqwKgBtDVgaGYmAD/v6XAYiQl7AAAAAElFTkSuQmCC')


class Icons1(flx.Widget):

    def init(self):
        flx.Button(text='Not much to see here ...')


class Icons2(flx.Widget):

    def init(self):
        self.set_title('Icon demo')
        self.set_icon(black_png)
        flx.Button(text='Not much to see here ...')


if __name__ == '__main__':

    # Select application icon. Can be a url, a relative url to a shared asset,
    # a base64 encoded image, or a local filename. Note that the local filename
    # works for setting the aplication icon in a desktop-like app, but not for
    # a web app. File types can be ico or png.

    # << Uncomment any of the lines below >>

    # icon = None  # use default
    # icon = 'https://assets-cdn.github.com/favicon.ico'
    # icon = flx.assets.add_shared_data('ico.icon', open(fname, 'rb').read())
    icon = black_png
    # icon = fname

    m = flx.App(Icons1, title='Icon demo', icon=icon).launch('app')
    flx.start()
