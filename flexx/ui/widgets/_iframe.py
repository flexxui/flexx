"""

Example:

.. UIExample:: 100
    
    with ui.BoxPanel():
        ui.IFrame(url='flexx.readthedocs.org')
        ui.IFrame(url='flexx.readthedocs.org')
"""

from ... import react
from ...pyscript import window
from . import Widget

 
class IFrame(Widget):
    """ An iframe element, i.e. a container to show web-content. 
    
    Note that some websites do not allow themselves to be rendered in
    a cross-source iframe.
    """
    
    CSS = '.flx-IFrame {border: none;}'
    
    @react.input
    def url(v=''):
        """ The url to show. 'http://' is automatically prepended if the url
        does not have '://' in it.
        """
        v = str(v)
        if v and '://' not in v:
            v = 'http://' + v
        return v
    
    class JS:
        
        def _create_node(self):
            self.p = window.phosphor.createWidget('iframe')
        
        @react.connect('url')
        def _update_url(self, url):
            print('set', url)
            self.node.src = url
