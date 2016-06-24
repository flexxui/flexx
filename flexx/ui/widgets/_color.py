"""

Simple example:

.. UIExample:: 50
    
    from flexx import ui, event
    
    class Example(ui.Widget):
        
        def init(self):
            self.c = ui.ColorSelectWidget()
        
        class JS:
            
            @event.connect('c.color')
            def _color_changed(self, *events):
                self.node.style.background = events[-1].new_value
"""

from ... import event
from ...pyscript import window
from . import Widget


class ColorSelectWidget(Widget):
    """ A widget used to select a color.
    
    This uses the HTML5 color input element, which is supported at least 
    on Firefox and Chrome, but not on IE/Edge last time I checked.
    """
    
    class Both:
            
        @event.prop
        def color(self, v='#000000'):
            """ The currently selected color.
            """
            if not (v.startswith('#') and len(v) == 7):
                raise ValueError('ColorSelectWidget must be in #rrggbb format.')
            return str(v)
    
    class JS:
    
        def _init_phosphor_and_node(self):
            self.phosphor = window.phosphor.createWidget('input')
            self.node = self.phosphor.node
            self.node.type = 'color'
            self.node.addEventListener('input', self._color_changed_from_dom, 0)
        
        @event.connect('color')
        def _color_changed(self, *events):
            self.node.value = self.color
        
        def _color_changed_from_dom(self, e):
            print('got event!!')
            self.color = self.node.value
