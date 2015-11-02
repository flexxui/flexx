"""

Simple example:

.. UIExample:: 50

    p = ui.ProgressBar(value=0.7)


Interactive example:

.. UIExample:: 100

    from flexx import app, ui, react
    
    class Example(ui.Widget):
    
        def init(self):
            with ui.HBox():
                self.b1 = ui.Button(flex=0, text='Less')
                self.b2 = ui.Button(flex=0, text='More')
                self.p = ui.ProgressBar(flex=1, value=0.1)
        
        class JS:
            
            @react.connect('b1.mouse_down', 'b2.mouse_down')
            def _change_progress(self, b1, b2):
                if b1:
                    self.p.value(self.p.value()-0.1)
                if b2:
                    self.p.value(self.p.value()+0.1)
"""

from ... import react
from ...pyscript.stubs import phosphor
from . import Widget


class ProgressBar(Widget):
    """ A widget to show progress.
    """
    
    CSS = ".flx-ProgressBar {min-height: 10px;}"
    
    @react.input
    def value(v=0):
        """ The progress value.
        """
        return float(v)
    
    @react.input
    def max(v=1):
        """ The maximum progress value.
        """
        return float(v)
    
    class JS:
    
        def _create_node(self):
            self.p = phosphor.createWidget('progress')
    
        @react.connect('value')
        def _value_changed(self, value):
            self.node.value = value
        
        @react.connect('max')
        def _max_changed(self, max_value):
            self.node.max = max_value
