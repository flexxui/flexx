# doc-export: SendData
"""
Example that demonstrates sending binray data from Python to JS. The
``Model.send_data()`` mechanism can be a powerful tool to send
(scientific) data, especially for large amounts of data. The method
accepts bytes or a URL ("http://" or "https://") where the
data can be retrieved. At his point AJAX is used to retrieve the data.
In the future we might push the data over a dedicated binary websocket
for greater performance.

If you find that you have a property that is a large list of numbers, maybe
that should be considered data instead of a property. 

Exported apps that use ``send_data()` work, but only if they are served
(e.g. on a blog, readthedocs or S3), because browsers typically refuse
to load local files via AJAX.
"""

from flexx import ui, app
from flexx.pyscript.stubs import window

try:
    import numpy as np
except ImportError:
    np = None


N = 1000

# Create array of N random float values. On numpy its easy
if np:
    data = np.random.normal(0, 1, N)
else:
    # fallback for when numpy is not avail
    import random
    import ctypes
    data = (ctypes.c_double * N)()
    for i in range(N):
        data[i] = random.random()


class SendData(ui.Widget):
    """ A simple example demonstrating sending binary data from Python to JS.
    """
    
    def init(self):
        self.label = ui.Label()
        self.style = 'overflow-y: scroll'  # enable scrolling
        
        # Send data to the JS side. In this case we don't need meta data
        meta = {}
        bb = data.tobytes() if hasattr(data, 'tobytes') else bytes(data)
        self.send_data(bb, meta)
    
    class JS:
        
        def receive_data(self, blob, meta):
            # This is the method to implement to handle received binary data
            
            # The first argument is an (untyped) arraybuffer,
            # we know its float64 in this case.
            data = window.Float64Array(blob)
            
            # Show the data as text. We could also e.g. plot it.
            text = ['%i: %f<br />' % (i, data[i]) for i in range(len(data))]
            header = 'This data was send in binary form:<br />'
            self.label.text = header + ''.join(text)


if __name__ == '__main__':
    m = app.launch(SendData)
    app.run()
