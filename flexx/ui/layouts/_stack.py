"""
Example:

.. UIExample:: 200
    
    from flexx import ui, react

    class Example(ui.Widget):
        def init(self):
            with ui.HBox():
                with ui.VBox():
                    self.buta = ui.Button(text='red')
                    self.butb = ui.Button(text='green')
                    self.butc = ui.Button(text='blue')
                    ui.Widget(flex=1)  # space filler
                with ui.StackedPanel(flex=1) as self.stack:
                    self.a = ui.Widget(style='background:#a00;')
                    self.b = ui.Widget(style='background:#0a0;')
                    self.c = ui.Widget(style='background:#00a;')
        
        class JS:
            
            @react.connect('buta.mouse_down', 'butb.mouse_down', 'butc.mouse_down')
            def _stacked_current(a, b, c):
                if a: self.stack.current(self.a)
                if b: self.stack.current(self.b)
                if c: self.stack.current(self.c)
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
