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
                    self.a = ui.Widget(style='background:#a00;')
                    self.b = ui.Widget(style='background:#0a0;')
                    self.c = ui.Widget(style='background:#00a;')
        
        class JS:
            
            @event.connect('buta.mouse_down', 'butb.mouse_down', 'butc.mouse_down')
            def _stacked_current(self, *events):
                ob = events[-1].source
                self.stack.current = ob
"""

from ... import event
from ...pyscript import window, this_is_js
from . import Widget, Layout


class StackedPanel(Layout):
    """ A panel which shows only one of its children at a time.
    """
    
    @event.prop
    def current(self, v=None):
        """ The currently shown widget.
        """
        if not (v is None or isinstance(v, Widget)):
            raise ValueError('The StackedPanel\'s current widget should be a Widget.')
        return v
    
    class JS:
        
        def init(self):
            self.p = window.phosphor.stackedpanel.StackedPanel()
        
        @event.connect('current')
        def __set_current_widget(self, *events):
            widget = events[-1].new_value
            for i in range(self.p.childCount()):
                self.p.childAt(i).hide()
            if widget is not None:
                widget.p.show()
                
