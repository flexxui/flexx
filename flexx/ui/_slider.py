"""

Simple example:

.. UIExample:: 50

    s = ui.Slider(min=10, max=20, value=12)


Interactive example:

.. UIExample:: 100

    from flexx import app, ui, react
    
    class Example(ui.Widget):
    
        def init(self):
            with ui.HBox():
                self.slider = ui.Slider(flex=0, min=1, max=20, step=1)
                self.label = ui.Label(flex=1)
        
        class JS:
            @react.connect('slider.value')
            def _change_label(self, value):
                self.label.text('x'.repeat(value))
"""

from .. import react
from . import Widget


class Slider(Widget):
    """ An input widget to select a value in a certain range (aka HTML
    range input).
    """
    
    CSS = ".flx-slider {min-height: 30px;}"
    
    @react.input
    def value(v=0):
        """ The current slider value (settable)."""
        return float(v)
    
    @react.input
    def step(v=0.01):
        """ The step size for the slider."""
        return float(v)
    
    @react.input
    def min(v=0):
        """ The minimal slider value."""
        return float(v)
    
    @react.input
    def max(v=1):
        """ The maximum slider value."""
        return float(v)
    
    class JS:
    
        def _create_node(self):
            self.node = document.createElement('input')
            self.node.type = 'range'
            that = self
            this.node.addEventListener('input', lambda ev: that.user_value._set(that.node.value), False)
            #if IE10:
            #    this.node.addEventListener('change', lambda ev: that.user_value._set(that.node.value), False)
            
        @react.source
        def user_value(v):
            """ The slider value set by the user (updates on user interaction). """
            if v is not undefined:
                v = float(v)
                self.value(v)
            return v
        
        @react.connect('value')
        def _value_changed(self, value):
            self.node.value = value
        
        @react.connect('step')
        def _step_changed(self, step):
            self.node.step= step
        
        @react.connect('min')
        def _min_changed(self, min_value):
            self.node.min = min_value
        
        @react.connect('max')
        def _max_changed(self, max_value):
            self.node.max = max_value
