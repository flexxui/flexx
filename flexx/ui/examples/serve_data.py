# doc-export: Example
"""
This example demonstrates how data can be provided to the client with the
Flexx asset management system.

There are two ways to provide data: via the asset store (``app.assets``),
and via the session (``some_model.session``). In the former, the data
is shared between sessions. In the latter, the data is specific for the
session (the link to the data includes the session id).

Note that ``add_shared_data()`` and ``add_data()`` both return the link
to the data for convenience. Shared data is always served at
'_data/shared/filename.ext', so we just use that explicitly here.

Similarly, the data provided by the server can be obtained using Ajax
(i.e. XMLHttpRequest).

Note that this example will only load random images if its live (i.e.
not exported).
"""

import random

import imageio

from flexx import app, event, ui
from flexx.util import png


# Define names of standard images
imageio_standard_images = ['clock.png', 'page.png', 'camera.png', 'coins.png',
                           'hubble_deep_field.png', 'text.png', 'chelsea.png',
                           'coffee.png', 'horse.png', 'wikkie.png', 'moon.png',
                           'astronaut.png', 'immunohistochemistry.png']

# Randomly select a shared image
fname = random.choice(imageio_standard_images)
image_data = png.write_png(imageio.imread(fname))
app.assets.add_shared_data('image.png', image_data)


class Example(ui.Widget):
    
    def init(self):
        
        # Randomly select image - different between sessions
        fname = random.choice(imageio_standard_images)
        image_data = png.write_png(imageio.imread(fname))
        link = self.session.add_data('image.png', image_data)

        # Create HTML with the two images
        html = '<p>Hit F5 to reload the page (i.e. create a new session'
        html += ', unless this is an exported app)</p>'
        html += '<p>This is session "%s"</p>' % self.session.id
        html += '<img src="%s" />' % "_data/shared/image.png"
        html += '<img src="%s" />' % link
        
        ui.Label(text=html, flex=1)


if __name__ == '__main__':
    # Launch the app twice to show how different sessions have different data
    m1 = app.launch(Example, 'browser')
    m2 = app.launch(Example, 'browser')
    app.run()
