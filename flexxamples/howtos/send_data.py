# doc-export: SendData
"""
Example that demonstrates sending (binary) array data from Python to JS.

The ``SendDataView`` widget (a ``JsComponent``) has an action to display the
data. This action is invoked from Python, with an array as input. The action
invokation is serialized with BSDF (http://bsdf.io), which natively supports
bytes and numpy arrays.

In this example we also provide a fallback for when Numpy is not available.
This fallback illustrates how any kind of data can be send to JS by providing
the serializer with an extension.
"""

from flexx import flx


# Prepare data array, preferably using Numpy
try:
    import numpy as np
    data_array = np.random.normal(0, 1, 1000)

except ImportError:
    # Fallback to ctypes when numpy is not available
    import random
    import ctypes
    from flexx.app import bsdf_lite

    # Create data array
    data_array = (ctypes.c_double * 1000)()
    for i in range(len(data_array)):
        data_array[i] = random.random()

    # Add extension that encodes a ctypes array to ndarray extension data
    @flx.serializer.add_extension
    class CtypesArrayExtension(bsdf_lite.Extension):

        name = 'ndarray'
        cls = ctypes.Array

        typemap = {
            ctypes.c_bool: 'uint8', ctypes.c_int8: 'int8', ctypes.c_uint8: 'uint8',
            ctypes.c_int16: 'int16', ctypes.c_uint16: 'uint16',
            ctypes.c_int32: 'int32', ctypes.c_uint32: 'uint32',
            ctypes.c_int64: 'int64', ctypes.c_uint64: 'uint64',
            ctypes.c_float: 'float32', ctypes.c_double: 'float64',
            }

        def encode(self, s, v):
            return dict(shape=(len(v), ),
                        dtype=self.typemap[v._type_],
                        data=bytes(v))


class SendData(flx.PyComponent):
    """ A simple example demonstrating sending binary data from Python to JS.
    """

    def init(self):
        self.view = SendDataView()
        self.view.set_data(data_array)


class SendDataView(flx.Widget):
    """ A widget that displays array data.
    """

    def init(self):
        self.label = flx.Label()
        self.apply_style('overflow-y: scroll;')  # enable scrolling

    @flx.action
    def set_data(self, data):
        # We receive the data as a typed array.
        # If we would send raw bytes, we would receive it as a DataView, which
        # we can map to e.g. a Int16Array like so:
        #   data = Int16Array(blob.buffer, blob.byteOffset, blob.byteLength/2)

        # Show the data as text. We could also e.g. plot it.
        text = ['%i: %f<br />' % (i, data[i]) for i in range(len(data))]
        header = 'This data (%i elements) was send in binary form:<br />' % len(data)
        self.label.set_html(header + ''.join(text))


if __name__ == '__main__':
    m = flx.launch(SendData, 'app')
    flx.run()
