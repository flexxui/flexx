"""

Simple example:

.. UIExample:: 50

    line = ui.LineEdit(text='edit me')


Interactive example:

.. UIExample:: 100

    from flexx import app, ui, react
    
    class Example(ui.Widget):
    
        def init(self):
            with ui.VBox():
                self.line = ui.LineEdit(flex=0,
                                        placeholder_text='type here',
                                        autocomp=['foo', 'bar'])
                ui.Label(flex=0, text='copy:')
                self.label = ui.Label(flex=1)
        
        class JS:
            @react.connect('line.text')
            def _change_label(self, value):
                self.label.text(value)
"""

from .. import react
from . import Widget


class LineEdit(Widget):
    """ An input widget to edit a line of text (aka HTML text input).
    """
    
    @react.input
    def text(v=''):
        """ The current text."""
        return str(v)
    
    @react.input
    def placeholder_text(v=''):
        """ The placeholder text (shown when the text is an empty string)."""
        return str(v)
    
    @react.input
    def autocomp(v=()):
        """ A tuple/list of strings for autocompletion. """
        return tuple([str(i) for i in v])
    
    class JS:
    
        def _create_node(self):
            self.node = document.createElement('div')
            self.node.innerHTML = '<input type="text", list="%s" />' % self.id
            self.node = self.node.childNodes[0]
            
            self._autocomp = document.createElement('datalist')
            self._autocomp.id = self.id
            self.node.appendChild(self._autocomp)
            
            that = self
            this.node.addEventListener('input', lambda ev: that.user_text._set(that.node.value), False)
            #if IE10:
            #    this.node.addEventListener('change', lambda ev: that.user_value._set(that.node.value), False)
            
        @react.source
        def user_text(v):
            """ The text set by the user (updates on each keystroke). """
            if v is not undefined:
                v = str(v)
                self.text(v)
            return v
        
        @react.connect('text')
        def _text_changed(self, text):
            self.node.value = text
        
        @react.connect('placeholder_text')
        def _placeholder_text_changed(self, text):
            self.node.placeholder = text
        
        @react.connect('autocomp')
        def _autocomp_changed(self, autocomp):
            # Clear
            for op in self._autocomp:
                self._autocomp.removeChild(op)
            # Add new options
            for option in autocomp:
                op = document.createElement('option')
                op.value = option
                self._autocomp.appendChild(op)
