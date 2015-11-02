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

from ... import react
from ...pyscript.stubs import document, undefined, phosphor
from . import Widget


class LineEdit(Widget):
    """ An input widget to edit a line of text (aka HTML text input).
    """
    
    CSS = """
    .flx-LineEdit > input-ttt { /* gets to be too wide */
        width: 100%;
    }
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
        """ A tuple/list of strings for autocompletion. Might not work
        in all browsers.
        """
        return tuple([str(i) for i in v])
    
    class JS:
    
        def _create_node(self):
            self.p = phosphor.createWidget('div')
            self.p.node.innerHTML = '<input type="text", list="%s" />' % self.id
            self._node = self.p.node.childNodes[0]
            
            # self.p = phosphor.createWidget('input')
            # self.node = self.p.node
            # self.node.type = 'text'
            # self.node.list = self.id
            
            self._autocomp = document.createElement('datalist')
            self._autocomp.id = self.id
            self._node.appendChild(self._autocomp)
            
            that = self
            f1 = lambda ev: that.user_text._set(that._node.value)
            f2 = lambda ev: that.submit._set(ev.which)
            self._node.addEventListener('input', f1, False)
            self._node.addEventListener('keydown', f2, False)
            #if IE10:
            #    this.node.addEventListener('change', f1, False)
            
        @react.source
        def user_text(self, v):
            """ The text set by the user (updates on each keystroke). """
            if v is not undefined:
                v = str(v)
                self.text(v)
            return v
        
        @react.source
        def submit(self, key=None):
            """ The user strikes the enter or return key. """
            if key == 13:
                return True
            elif key is None:
                return False  # init the value
            return undefined
        
        @react.connect('text')
        def _text_changed(self, text):
            self._node.value = text
        
        @react.connect('placeholder_text')
        def _placeholder_text_changed(self, text):
            self._node.placeholder = text
        
        # todo: this works in Firefox but not in Xul
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
