"""

Example:

.. UIExample:: 100
    
    with ui.BoxPanel():
        ui.IFrame(url='flexx.readthedocs.io')
        ui.IFrame(url='flexx.readthedocs.io')
"""

from ... import event
from . import Widget

 
class IFrame(Widget):
    """ An iframe element, i.e. a container to show web-content. 
    
    Note that some websites do not allow themselves to be rendered in
    a cross-source iframe.
    """
    
    CSS = '.flx-IFrame {border: none;}'
    
    class Both:
        
        @event.prop
        def url(self, v=''):
            """ The url to show. 'http://' is automatically prepended if the url
            does not have '://' in it.
            """
            v = str(v)
            if v and '://' not in v:
                v = 'http://' + v
            return v
    
    class JS:
        
        def _init_phosphor_and_node(self):
            self.phosphor = self._create_phosphor_widget('iframe')
            self.node = self.phosphor.node
        
        @event.connect('url')
        def _update_url(self, *events):
            self.node.src = self.url
