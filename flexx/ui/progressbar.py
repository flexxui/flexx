from ..properties import Float

from .widget import Widget, js


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
    value = Float(0)
    max_value = Float(1)
    
    @js
    def _js_create_node(self):
        self.node = document.createElement('progress')
    
    @js
    def _js_value_changed(self, name, old, value):
        self.node.value = value
    
    @js
    def _js_max_value_changed(self, name, old, max_value):
        self.node.max = max_value
  
