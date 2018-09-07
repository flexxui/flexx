""" Button classes

Simple example:

.. UIExample:: 50

    b = ui.Button(text="Push me")


Also see examples: :ref:`buttons.py`.

"""

from ... import event
from .._widget import Widget


class BaseButton(Widget):
    """ Abstract button class.
    """

    DEFAULT_MIN_SIZE = 10, 24

    CSS = """

    .flx-BaseButton {
        white-space: nowrap;
        padding: 0.2em 0.4em;
        border-radius: 3px;
        color: #333;
    }
    .flx-BaseButton, .flx-BaseButton > input {
        margin: 2px; /* room for outline */
    }
    .flx-BaseButton:focus, .flx-BaseButton > input:focus  {
        outline: none;
        box-shadow: 0px 0px 3px 1px rgba(0, 100, 200, 0.7);
    }

    .flx-Button, .flx-ToggleButton{
        background: #e8e8e8;
        border: 1px solid #ccc;
        transition: background 0.3s;
    }
    .flx-Button:hover, .flx-ToggleButton:hover {
        background: #e8eaff;
    }

    .flx-ToggleButton {
        text-align: left;
    }
    .flx-ToggleButton.flx-checked {
        background: #e8eaff;
    }
    .flx-ToggleButton::before {
        content: '\\2610\\00a0 ';
    }
    .flx-ToggleButton.flx-checked::before {
        content: '\\2611\\00a0 ';
    }

    .flx-RadioButton > input, .flx-CheckBox > input{
        margin-left: 0.3em;
        margin-right: 0.3em;
    }

    .flx-RadioButton > input, .flx-CheckBox > input {
        color: #333;
    }
    .flx-RadioButton:hover > input, .flx-CheckBox:hover > input {
        color: #036;
    }
    """

    text = event.StringProp('', settable=True, doc="""
        The text on the button.
        """)

    checked = event.BoolProp(False, settable=True, doc="""
        Whether the button is checked.
        """)

    disabled = event.BoolProp(False, settable=True, doc="""
        Whether the button is disabled.
        """)

    @event.reaction('pointer_click')
    def __on_pointer_click(self, e):
        self.node.blur()

    @event.emitter
    def user_checked(self, checked):
        """ Event emitted when the user (un)checks this button. Has
        ``old_value`` and ``new_value`` attributes.
        """
        d = {'old_value': self.checked, 'new_value': checked}
        self.set_checked(checked)
        return d


class Button(BaseButton):
    """ A push button.
    
    The ``node`` of this widget is a
    `<button> <https://developer.mozilla.org/docs/Web/HTML/Element/button>`_.
    """

    DEFAULT_MIN_SIZE = 10, 28

    def _create_dom(self):
        global window
        node = window.document.createElement('button')
        # node = window.document.createElement('input')
        # node.setAttribute('type', 'button')
        return node

    def _render_dom(self):
        return [self.text]

    @event.reaction('disabled')
    def __disabled_changed(self, *events):
        if events[-1].new_value:
            self.node.setAttribute("disabled", "disabled")
        else:
            self.node.removeAttribute("disabled")


class ToggleButton(BaseButton):
    """ A button that can be toggled. It behaves like a checkbox, while
    looking more like a regular button.
    
    The ``node`` of this widget is a
    `<button> <https://developer.mozilla.org/docs/Web/HTML/Element/button>`_.
    """

    DEFAULT_MIN_SIZE = 10, 28

    def _create_dom(self):
        global window
        node = window.document.createElement('button')
        return node

    def _render_dom(self):
        return [self.text]

    @event.reaction('pointer_click')
    def __toggle_checked(self, *events):
        self.user_checked(not self.checked)

    @event.reaction('checked')
    def __check_changed(self, *events):
        if self.checked:
            self.node.classList.add('flx-checked')
        else:
            self.node.classList.remove('flx-checked')


class RadioButton(BaseButton):
    """ A radio button. Of any group of radio buttons that share the
    same parent, only one can be active.
    
    The ``outernode`` of this widget is a
    `<label> <https://developer.mozilla.org/docs/Web/HTML/Element/label>`_,
    and the ``node`` a radio
    `<input> <https://developer.mozilla.org/docs/Web/HTML/Element/input>`_.
    """

    def _create_dom(self):
        global window
        outernode = window.document.createElement('label')
        node = window.document.createElement('input')
        outernode.appendChild(node)

        node.setAttribute('type', 'radio')
        node.setAttribute('id', self.id)
        outernode.setAttribute('for', self.id)

        return outernode, node

    def _render_dom(self):
        return [self.node, self.text]

    @event.reaction('parent')
    def __update_group(self, *events):
        if self.parent:
            self.node.name = self.parent.id

    @event.reaction('checked')
    def __check_changed(self, *events):
        self.node.checked = self.checked

    @event.emitter
    def pointer_click(self, e):
        """ This method is called on JS a click event. We *first* update
        the checked properties, and then emit the Flexx click event.
        That way, one can connect to the click event and have an
        up-to-date checked props (even on Py).
        """
        # Turn off any radio buttons in the same group
        if self.parent:
            for child in self.parent.children:
                if isinstance(child, RadioButton) and child is not self:
                    child.set_checked(child.node.checked)
        # Turn on this button (last)
        self.user_checked(self.node.checked)  # instead of set_checked
        # Process actual click event
        super().pointer_click(e)


class CheckBox(BaseButton):
    """ A checkbox button.
    
    The ``outernode`` of this widget is a
    `<label> <https://developer.mozilla.org/docs/Web/HTML/Element/label>`_,
    and the ``node`` a checkbox
    `<input> <https://developer.mozilla.org/docs/Web/HTML/Element/input>`_.
    """

    def _create_dom(self):
        global window
        outernode = window.document.createElement('label')
        node = window.document.createElement('input')
        outernode.appendChild(node)

        node.setAttribute('type', 'checkbox')
        node.setAttribute('id', self.id)
        outernode.setAttribute('for', self.id)
        self._addEventListener(node, 'click', self._check_changed_from_dom, 0)

        return outernode, node

    def _render_dom(self):
        return [self.node, self.text]

    @event.reaction('checked')
    def __check_changed(self, *events):
        self.node.checked = self.checked

    def _check_changed_from_dom(self, ev):
        self.user_checked(self.node.checked)
