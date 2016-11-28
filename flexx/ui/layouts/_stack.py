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
from ...pyscript import RawJS
from . import Widget, Layout


_phosphor_stackedpanel = RawJS("flexx.require('phosphor/lib/ui/stackedpanel')")
_phosphor_iteration = RawJS("flexx.require('phosphor/lib/algorithm/iteration')")


class StackedPanel(Layout):
    """ A panel which shows only one of its children at a time.
    """
    
    class Both:
        
        @event.prop
        def current(self, v=None):
            """ The currently shown widget.
            """
            if not (v is None or isinstance(v, Widget)):
                raise ValueError("%s.current should be a Widget, not %r" % (self.id, v))
            return v
    
    class JS:
        
        def _init_phosphor_and_node(self):
            self.phosphor = _phosphor_stackedpanel.StackedPanel()
            self.node = self.phosphor.node
        
        @event.connect('current')
        def __set_current_widget(self, *events):
            widget = events[-1].new_value
            _phosphor_iteration.each(self.phosphor.widgets, lambda w: w.hide())
            if widget is not None:
                widget.phosphor.show()
