
from .. import react

from .widget import Widget


class ProgressBar(Widget):
    """ A widget to show progress.
    
    Example:
    
    .. UIExample:: 100
    
        from flexx import ui
        
        class App(ui.App):
            def init(self):
                with ui.HBox():  # show our widget full-window
                    ui.ProgressBar(flex=1, value=0.7)
    
    """
    
    CSS = ".flx-progressbar {min-height: 10px;}"
    
    @react.input
    def value(v=0):
        """ The progress value.
        """
        return float(v)
    
    @react.input
    def max_value(v=1):
        """ The maximum progress value.
        """
        return float(v)
    
    class JS:
    
        def _create_node(self):
            self.node = document.createElement('progress')
    
        @react.act('value')
        def _value_changed(self, value):
            self.node.value = value
        
        @react.act('max_value')
        def _max_value_changed(self, max_value):
            self.node.max = max_value

