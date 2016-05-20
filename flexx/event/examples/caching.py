"""
Caching example. The object has a readonly property "data", that gets
automatically set when the "source" property gets set. The
download_data handler takes care of updating data when necesary.

This example aims for an analog of "streams" as they are used in
reactive programming. In RP, the data property would be a signal
connected to source and would contain the logic that is now in
download_data,
"""

import time
from flexx import event


class CachingExample(event.HasEvents):
    
    @event.prop
    def source(self, v=''):
        """ The input for the calcualations. """
        return str(v)
    
    @event.connect('source')
    def download_data(self, *events):
        """ Simulate a download of data from the web. takes a while. """
        if self.source:
            time.sleep(2)
            self._set_prop('data', hash(self.source))
    
    @event.readonly
    def data(self, v=None):
        """ readonly prop to cache the result. """
        return v
    
    @event.connect('data')
    def show_data(self, *events):
        """ handler to show the data. Can be called at any time. """
        if self.data is not None:
            print('The data is', self.data)


c = CachingExample()

c.source = 'foo'

event.loop.iter()
