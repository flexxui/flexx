"""
Example:

.. UIExample:: 200
    
    from flexx import ui, event

    class Example(ui.Widget):
        def init(self):
            with ui.HBox():
                with ui.VBox():
                    self.buta = ui.Button(text='red')
                    self.butb = ui.Button(text='green')
                    self.butc = ui.Button(text='blue')
                    ui.Widget(flex=1)  # space filler
                with ui.StackedPanel(flex=1) as self.stack:
                    self.buta.w = ui.Widget(style='background:#a00;')
                    self.butb.w = ui.Widget(style='background:#0a0;')
                    self.butc.w = ui.Widget(style='background:#00a;')
        
        class JS:
            
            @event.connect('buta.mouse_down', 'butb.mouse_down', 'butc.mouse_down')
            def _stacked_current(self, *events):
                button = events[-1].source
                self.stack.current = button.w
"""

from ... import event
from ...pyscript import window
from . import Widget, Layout


class StackedPanel(Layout):
    """ A panel which shows only one of its children at a time.
    """
    
    class Both:
        
        @event.prop
        def current(self, v=None):
            """ The currently shown widget.
            """
            if not (v is None or isinstance(v, Widget)):
                raise ValueError("The StackedPanel's current widget " +
                                 "should be a Widget.")
            return v
    
    class JS:
        
        def _init_phosphor_and_node(self):
            self.phosphor = window.phosphor.stackedpanel.StackedPanel()
            self.node = self.phosphor.node
        
        @event.connect('current')
        def __set_current_widget(self, *events):
            widget = events[-1].new_value
            for i in range(self.phosphor.childCount()):
                self.phosphor.childAt(i).hide()
            if widget is not None:
                widget.phosphor.show()
