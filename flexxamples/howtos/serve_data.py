# doc-export: Example
"""
This example demonstrates how data can be provided to the client with the
Flexx asset management system.

There are two ways to provide data: via the asset store (``flx.assets``),
and via the session (``some_model.session``). In the former, the data
is shared between sessions. In the latter, the data is specific for the
session (the link to the data includes the session id).

Note that ``add_shared_data()`` and ``add_data()`` both return the link
to the data for convenience. Shared data is served at
'/flexx/data/shared/filename.ext', though one can also use the relative path
'_data/shared/filename.ext', which also works for exported apps.

Similarly, the data provided by the server can be obtained using Ajax
(i.e. XMLHttpRequest).

Note that this example will only load random images if its live (i.e.
not exported).

See video_viewer.py for an example on providing data without reading it
in memory.
"""

import random
from urllib.request import urlopen

from flexx import flx


# Define names of standard images
image_names = ['clock.png', 'page.png', 'camera.png', 'coins.png',
               'hubble_deep_field.png', 'text.png', 'chelsea.png',
               'coffee.png', 'horse.png', 'wikkie.png', 'moon.png',
               'astronaut.png', 'immunohistochemistry.png']


def get_img_blob(name):
    """ Given an image name, download the raw bytes from imageio's repository
    of standard images.
    """
    url_root = 'https://github.com/imageio/imageio-binaries/raw/master/images/'
    return urlopen(url_root + name, timeout=2.0).read()


# Randomly select a shared image at server start
link1 = flx.assets.add_shared_data('image.png',
                                   get_img_blob(random.choice(image_names)))


class Example(flx.PyWidget):

    def init(self):
        # Randomly select image - different between sessions
        link2 = self.session.add_data('image.png',
                                      get_img_blob(random.choice(image_names)))

        # Create widget to show images
        View(link1, link2)


class View(flx.Label):
    def init(self, link1, link2):
        html = '<p>Hit F5 to reload the page (i.e. create a new session'
        html += ', unless this is an exported app)</p>'
        html += '<p>This is session "%s"</p>' % self.session.id
        html += '<img src="%s" />' % link1
        html += '<img src="%s" />' % link2
        self.set_html(html)


if __name__ == '__main__':
    # Launch the app twice to show how different sessions have different data
    a = flx.App(Example)
    m1 = a.launch('browser')
    m2 = a.launch('browser')
    flx.run()
