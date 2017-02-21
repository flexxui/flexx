"""

Simple example:

.. UIExample:: 50

    line = ui.LineEdit(text='edit me')


Interactive example:

.. UIExample:: 100

    from flexx import app, ui, event
    
    class Example(ui.Widget):
    
        def init(self):
            with ui.VBox():
                self.line = ui.LineEdit(flex=0,
                                        placeholder_text='type here',
                                        autocomp=['foo', 'bar'])
                ui.Label(flex=0, text='copy:')
                self.label = ui.Label(flex=1)
        
        class JS:
            @event.connect('line.text')
            def _change_label(self, *events):
                self.label.text = events[-1].new_value
"""

from ... import event
from ...pyscript import window, RawJS
from . import Widget


_phosphor_widget = RawJS("flexx.require('phosphor/lib/ui/widget')")


class LineEdit(Widget):
    """ An input widget to edit a line of text (aka HTML text input).
    """
    
    CSS = """
    .flx-LineEdit > input {
        max-width: none;
        min-width: 2em;
    }
    """
    
    class Both:
            
        @event.prop
        def text(self, v=''):
            """ The current text."""
            return str(v)
        
        @event.prop
        def password_mode(self, v=False):
            """ Whether the insered text should be hidden or not.
            """
            return bool(v)
        
        @event.prop
        def placeholder_text(self, v=''):
            """ The placeholder text (shown when the text is an empty string)."""
            return str(v)
        
        @event.prop
        def autocomp(self, v=()):
            """ A tuple/list of strings for autocompletion. Might not work
            in all browsers.
            """
            return tuple([str(i) for i in v])

        @event.prop
        def disabled(self, v=False):
            """ Whether the line edit is disabled.
            """
            return bool(v)

    class JS:
    
        def _init_phosphor_and_node(self):
            
            # Create node element
            d = window.document.createElement('div')
            d.innerHTML = '<input type="text", list="%s" />' % self.id
            node = d.childNodes[0]
            
            # Wrap up in Phosphor
            self.phosphor = _phosphor_widget.Widget({'node': node})
            self.node = self.phosphor.node
            
            self._autocomp = window.document.createElement('datalist')
            self._autocomp.id = self.id
            self.node.appendChild(self._autocomp)
            
            f1 = lambda ev: self._set_prop('user_text', self.node.value)
            f2 = lambda ev: self.submit() if ev.which == 13 else None
            self.node.addEventListener('input', f1, False)
            self.node.addEventListener('keydown', f2, False)
            #if IE10:
            #    this.node.addEventListener('change', f1, False)
        
        @event.readonly
        def user_text(self, v=None):
            """ The text set by the user (updates on each keystroke). """
            if v is not None:
                v = str(v)
                self.text = v
            return v
        
        @event.emitter
        def submit(self):
            """ Event emitted when the user strikes the enter or return key.
            """
            return {}
        
        @event.connect('text')
        def __text_changed(self, *events):
            self.node.value = self.text
        
        @event.connect('password_mode')
        def __password_mode_changed(self, *events):
            self.node.type = ['text', 'password'][int(bool(self.password_mode))]
        
        @event.connect('placeholder_text')
        def __placeholder_text_changed(self, *events):
            self.node.placeholder = self.placeholder_text
        
        # todo: this works in the browser but not in e.g. firefox-app
        @event.connect('autocomp')
        def __autocomp_changed(self, *events):
            autocomp = self.autocomp
            # Clear
            for op in self._autocomp:
                self._autocomp.removeChild(op)
            # Add new options
            for option in autocomp:
                op = window.document.createElement('option')
                op.value = option
                self._autocomp.appendChild(op)

        @event.connect('disabled')
        def __disabled_changed(self, *events):
            if events[-1].new_value:
                self.node.setAttribute("disabled", "disabled")
            else:
                self.node.removeAttribute("disabled")
