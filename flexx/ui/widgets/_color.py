""" ColorSelectWidget

.. UIExample:: 50
    
    from flexx import ui, event
    
    class Example(ui.Widget):
        
        def init(self):
            self.c = ui.ColorSelectWidget()
    
        @event.reaction
        def _color_changed(self):
            self.node.style.background = self.c.color
"""

from ... import event
from . import Widget


class ColorSelectWidget(Widget):
    """ A widget used to select a color.
    
    This uses the HTML5 color input element, which is supported at least 
    on Firefox and Chrome, but not on IE/Edge last time I checked.
    """
    
    color = event.StringProp('#000000', settable=False, doc="""
        The currently selected color.
        """)
    
    disabled = event.BoolProp(False, settable=True, doc="""
        Whether the color select is disabled.
        """)
    
    @event.action
    def set_color(self, v):
        """ Set the color property as a HTML hex color.
        """
        v = str(v)
        if not (v.startswith('#') and len(v) == 7):
            raise ValueError('%s.color must be in #rrggbb format, not %r' %
                             (self.id, v))
        self._mutate_color(v)
    
    def _create_dom(self):
        global window
        node = window.document.createElement('input')
        node.type = 'color'
        self._addEventListener(node, 'input', self._color_changed_from_dom, 0)
        return node
    
    @event.reaction('color')
    def _color_changed(self, *events):
        self.node.value = self.color
    
    def _color_changed_from_dom(self, e):
        self.set_color(self.node.value)

    @event.reaction('disabled')
    def __disabled_changed(self, *events):
        if self.disabled:
            self.node.setAttribute("disabled", "disabled")
        else:
            self.node.removeAttribute("disabled")
