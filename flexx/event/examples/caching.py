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


class CachingExample(event.Component):
    
    source = event.prop('', setter=str, doc='The input for the calculations.')
    data = event.prop(None, setter=lambda x:x, doc='Cache of the calculation result.')
    
    @event.reaction('source')
    def download_data(self, *events):
        """ Simulate a download of data from the web. takes a while. """
        if self.source:
            time.sleep(2)
            self.set_data(hash(self.source))
    
    @event.reaction
    def show_data(self, *events):
        """ handler to show the data. Can be called at any time. """
        if self.data is not None:
            print('The data is', self.data)


c = CachingExample()

c.set_source('foo')

event.loop.iter()
