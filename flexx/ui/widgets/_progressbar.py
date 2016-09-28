"""

Simple example:

.. UIExample:: 50

    p = ui.ProgressBar(value=0.7)


Interactive example:

.. UIExample:: 100

    from flexx import app, ui, event
    
    class Example(ui.Widget):
    
        def init(self):
            with ui.HBox():
                self.b1 = ui.Button(flex=0, text='Less')
                self.b2 = ui.Button(flex=0, text='More')
                self.prog = ui.ProgressBar(flex=1, value=0.1)
        
        class JS:
            
            @event.connect('b1.mouse_down', 'b2.mouse_down')
            def _change_progress(self, *events):
                for ev in events:
                    if ev.source is self.b1:
                        self.prog.value -= 0.1
                    else:
                        self.prog.value += 0.1
"""

from ... import event
from . import Widget


class ProgressBar(Widget):
    """ A widget to show progress.
    """
    
    CSS = ".flx-ProgressBar {min-height: 10px;}"
    
    class Both:
            
        @event.prop
        def value(self, v=0):
            """ The progress value.
            """
            return float(v)
        
        @event.prop
        def max(self, v=1):
            """ The maximum progress value.
            """
            return float(v)
    
    class JS:
    
        def _init_phosphor_and_node(self):
            self.phosphor = self._create_phosphor_widget('progress')
            self.node = self.phosphor.node
        
        @event.connect('value')
        def __value_changed(self, *events):
            self.node.value = events[-1].new_value
        
        @event.connect('max')
        def __max_changed(self, *events):
            self.node.max = events[-1].new_value
