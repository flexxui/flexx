"""

"""

from ... import react
from . import Widget, Layout


class StackedPanel(Layout):
    """ A panel which shows only one of its children at a time.
    """
    
    @react.input
    def current(v=None):
        """ The currently shown widget.
        """
        if not isinstance(v, Widget):
            raise ValueError('The StackedPanel\'s current widget should be a Widget.')
        return v
    
    
    class JS:
        
        def _create_node(self):
            self.p = phosphor.stackedpanel.StackedPanel()
        
        @react.connect('current')
        def __set_current_widget(self, widget):
            self.p.currentWidget = widget.p
