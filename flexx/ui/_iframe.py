from .. import react
from . import Widget

 
class IFrame(Widget):
    """ An iframe element, i.e. a container to show web-content. Note
    that some websites do not allow themselves to be rendered in a
    cross-source iframe.
    """
    
    CSS = '.flx-iframe {border: none;}'
    
    @react.input
    def url(v=''):
        """ The url to show. 'http://' is automatically prepended if the url
        does not have '://' in it.
        """
        v = str(v)
        if v and not '://' in v:
            v = 'http://' + v
        return v
    
    class JS:
        
        def _create_node(self):
            self.node = document.createElement('iframe')
        
        @react.connect('url')
        def _update_url(self, url):
            print('set', url)
            self.node.src = url
