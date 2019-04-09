"""

The ``LineEdit`` and ``MultiLineEdit`` widgets provide a way for the user
to input text.


.. UIExample:: 100

    from flexx import app, event, ui

    class Example(ui.Widget):

        def init(self):
            with ui.VBox():
                self.line = ui.LineEdit(placeholder_text='type here')
                self.l1 = ui.Label(html='<i>when user changes text</i>')
                self.l2 = ui.Label(html='<i>when unfocusing or hitting enter </i>')
                self.l3 = ui.Label(html='<i>when submitting (hitting enter)</i>')
                ui.Widget(flex=1)

        @event.reaction('line.user_text')
        def when_user_changes_text(self, *events):
            self.l1.set_text('user_text: ' + self.line.text)

        @event.reaction('line.user_done')
        def when_user_is_done_changing_text(self, *events):
            self.l2.set_text('user_done: ' + self.line.text)

        @event.reaction('line.submit')
        def when_user_submits_text(self, *events):
            self.l3.set_text('submit: ' + self.line.text)

"""

from ... import event
from . import Widget


class LineEdit(Widget):
    """ An input widget to edit a line of text.

    The ``node`` of this widget is a text
    `<input> <https://developer.mozilla.org/docs/Web/HTML/Element/input>`_.
    """

    DEFAULT_MIN_SIZE = 100, 28

    CSS = """
    .flx-LineEdit {
        color: #333;
        padding: 0.2em 0.4em;
        border-radius: 3px;
        border: 1px solid #aaa;
        margin: 2px;
    }
    .flx-LineEdit:focus  {
        outline: none;
        box-shadow: 0px 0px 3px 1px rgba(0, 100, 200, 0.7);
    }
    """

    ## Properties

    text = event.StringProp(settable=True, doc="""
        The current text of the line edit. Settable. If this is an empty
        string, the placeholder_text is displayed instead.
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

    def _create_dom(self):
        global window

        # Create node element
        node = window.document.createElement('input')
        node.setAttribute('type', 'input')
        node.setAttribute('list', self.id)

        self._autocomp = window.document.createElement('datalist')
        self._autocomp.id = self.id
        node.appendChild(self._autocomp)

        f1 = lambda: self.user_text(self.node.value)
        self._addEventListener(node, 'input', f1, False)
        self._addEventListener(node, 'blur', self.user_done, False)
        #if IE10:
        #    self._addEventListener(self.node, 'change', f1, False)
        return node

    @event.emitter
    def user_text(self, text):
        """ Event emitted when the user edits the text. Has ``old_value``
        and ``new_value`` attributes.
        """
        d = {'old_value': self.text, 'new_value': text}
        self.set_text(text)
        return d

    @event.emitter
    def user_done(self):
        """ Event emitted when the user is done editing the text, either by
        moving the focus elsewhere, or by hitting enter.
        Has ``old_value`` and ``new_value`` attributes (which are the same).
        """
        d = {'old_value': self.text, 'new_value': self.text}
        return d

    @event.emitter
    def submit(self):
        """ Event emitted when the user strikes the enter or return key
        (but not when losing focus). Has ``old_value`` and ``new_value``
        attributes (which are the same).
        """
        self.user_done()
        d = {'old_value': self.text, 'new_value': self.text}
        return d

    @event.emitter
    def key_down(self, e):
        # Prevent propating the key
        ev = super().key_down(e)
        pkeys = 'Escape',  # keys to propagate
        if (ev.modifiers and ev.modifiers != ('Shift', )) or ev.key in pkeys:
            pass
        else:
            e.stopPropagation()
        if ev.key in ('Enter', 'Return'):
            self.submit()
            # Nice to blur on mobile, since it hides keyboard, but less nice on desktop
            # self.node.blur()
        elif ev.key == 'Escape':
            self.node.blur()
        return ev

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

    # note: this works in the browser but not in e.g. firefox-app
    @event.reaction
    def __autocomp_changed(self):
        global window
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


class MultiLineEdit(Widget):
    """ An input widget to edit multiple lines of text.

    The ``node`` of this widget is a
    `<textarea> <https://developer.mozilla.org/docs/Web/HTML/Element/textarea>`_.
    """

    DEFAULT_MIN_SIZE = 100, 50

    CSS = """
        .flx-MultiLineEdit {
            resize: none;
            overflow-y: scroll;
            color: #333;
            padding: 0.2em 0.4em;
            border-radius: 3px;
            border: 1px solid #aaa;
            margin: 2px;
        }
        .flx-MultiLineEdit:focus  {
            outline: none;
            box-shadow: 0px 0px 3px 1px rgba(0, 100, 200, 0.7);
        }
    """

    text = event.StringProp(settable=True, doc="""
        The current text of the multi-line edit. Settable. If this is an empty
        string, the placeholder_text is displayed instead.
        """)

    def _create_dom(self):
        node = window.document.createElement('textarea')
        f1 = lambda: self.user_text(self.node.value)
        self._addEventListener(node, 'input', f1, False)
        self._addEventListener(node, 'blur', self.user_done, False)
        return node

    @event.reaction
    def __text_changed(self):
        self.node.value = self.text

    @event.emitter
    def user_text(self, text):
        """ Event emitted when the user edits the text. Has ``old_value``
        and ``new_value`` attributes.
        """
        d = {'old_value': self.text, 'new_value': text}
        self.set_text(text)
        return d

    @event.emitter
    def user_done(self):
        """ Event emitted when the user is done editing the text by
        moving the focus elsewhere. Has ``old_value`` and ``new_value``
        attributes (which are the same).
        """
        d = {'old_value': self.text, 'new_value': self.text}
        return d
