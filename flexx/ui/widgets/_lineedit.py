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
        
        @event.reaction
        def __change_label(self):
            self.label.set_text(self.line.text)
"""

from ... import event
from ...pyscript import window, RawJS
from . import Widget


# _phosphor_widget = RawJS("flexx.require('phosphor/lib/ui/widget')")


class LineEdit(Widget):
    """ An input widget to edit a line of text (aka HTML text input).
    """
    
    CSS = """
    .flx-LineEdit > input {
        max-width: none;
        min-width: 2em;
    }
    """
    
    ## Properties
    
    text = event.StringProp(settable=True, doc="""
        The current text of the line edit. Settable. If this is an empty
        string, the placeholder_text is displayed instead.
        """)
    
    user_text = event.StringProp(settable=False, doc="""
        The text set by the user (updates on each keystroke).
        """)
    
    password_mode = event.BoolProp(False, settable=True, doc="""
        Whether the insered text should be hidden.
        """)
    
    placeholder_text = event.StringProp(settable=True, doc="""
        The placeholder text (shown when the text is an empty string).
        """)
    
    autocomp = event.TupleProp(settable=True, doc="""
        A tuple/list of strings for autocompletion. Might not work in all browsers.
        """)
    
    disabled = event.BoolProp(False, settable=True, doc="""
        Whether the line edit is disabled.
        """)
    
    ## Methods, actions, emitters
    
    def _init_dom(self):
        
        # Create node element
        d = window.document.createElement('div')
        d.innerHTML = '<input type="text", list="%s" />' % self.id
        self.node = d.childNodes[0]
        self.outernode = self.node
        
        self._autocomp = window.document.createElement('datalist')
        self._autocomp.id = self.id
        self.node.appendChild(self._autocomp)
        
        f1 = self._set_user_text
        f2 = lambda ev: self.submit() if ev.which == 13 else None
        self._addEventListener(self.node, 'input', f1, False)
        self._addEventListener(self.node, 'keydown', f2, False)
        #if IE10:
        #    self._addEventListener(self.node, 'change', f1, False)
    
    @event.action
    def _set_user_text(self):
        text = self.node.value
        self._mutate_user_text(text)
        self._mutate_text(text)
    
    @event.emitter
    def key_down(self, e):
        # Prevent propating the key
        ev = super().key_down(e)
        pkeys = 'Escape',  # keys to propagate
        if (ev.modifiers and ev.modifiers != ('Shift', )) or ev.key in pkeys:
            pass
        else:
            e.stopPropagation()
        return ev
    
    @event.emitter
    def submit(self):
        """ Event emitted when the user strikes the enter or return key.
        """
        return {}
    
    ## Reactions
    
    @event.reaction
    def __text_changed(self):
        self.node.value = self.text
    
    @event.reaction
    def __password_mode_changed(self):
        self.node.type = ['text', 'password'][int(bool(self.password_mode))]
    
    @event.reaction
    def __placeholder_text_changed(self):
        self.node.placeholder = self.placeholder_text
    
    # todo: this works in the browser but not in e.g. firefox-app
    @event.reaction
    def __autocomp_changed(self):
        autocomp = self.autocomp
        # Clear
        for op in self._autocomp:
            self._autocomp.removeChild(op)
        # Add new options
        for option in autocomp:
            op = window.document.createElement('option')
            op.value = option
            self._autocomp.appendChild(op)

    @event.reaction
    def __disabled_changed(self):
        if self.disabled:
            self.node.setAttribute("disabled", "disabled")
        else:
            self.node.removeAttribute("disabled")
