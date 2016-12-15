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
            v = str(v)
            if not (v.startswith('#') and len(v) == 7):
                raise ValueError('%s.color must be in #rrggbb format, not %r' %
                                 (self.id, v))
            return str(v)

        @event.prop
        def disabled(self, v=False):
            """ Whether the color select is disabled.
            """
            return bool(v)

    class JS:
    
        def _init_phosphor_and_node(self):
            self.phosphor = self._create_phosphor_widget('input')
            self.node = self.phosphor.node
            self.node.type = 'color'
            self.node.addEventListener('input', self._color_changed_from_dom, 0)
        
        @event.connect('color')
        def _color_changed(self, *events):
            self.node.value = self.color
        
        def _color_changed_from_dom(self, e):
            self.color = self.node.value

        @event.connect('disabled')
        def __disabled_changed(self, *events):
            if events[-1].new_value:
                self.node.setAttribute("disabled", "disabled")
            else:
                self.node.removeAttribute("disabled")
