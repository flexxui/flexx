""" ColorSelectWidget

.. UIExample:: 50

    from flexx import event, ui

    class Example(ui.Widget):

        def init(self):
            self.c = ui.ColorSelectWidget()

        @event.reaction
        def _color_changed(self):
            self.node.style.background = self.c.color.hex
"""

from ... import event
from . import Widget


class ColorSelectWidget(Widget):
    """ A widget used to select a color.

    The ``node`` of this widget is an
    `<input> <https://developer.mozilla.org/docs/Web/HTML/Element/input>`_
    element of type ``color``. This is supported at least
    on Firefox and Chrome, but not on IE.
    """

    DEFAULT_MIN_SIZE = 28, 28

    color = event.ColorProp('#000000', settable=True, doc="""
        The currently selected color.
        """)

    disabled = event.BoolProp(False, settable=True, doc="""
        Whether the color select is disabled.
        """)

    def _create_dom(self):
        global window
        node = window.document.createElement('input')
        try:
            node.type = 'color'
        except Exception:  # This widget simply does not work on IE
            node = window.document.createElement('div')
            node.innerHTML = 'Not supported'
        self._addEventListener(node, 'input', self._color_changed_from_dom, 0)
        return node

    @event.emitter
    def user_color(self, color):
        """ Event emitted when the user changes the color. Has ``old_value``
        and ``new_value`` attributes.
        """
        d = {'old_value': self.color, 'new_value': color}
        self.set_color(color)
        return d

    @event.reaction('color')
    def _color_changed(self, *events):
        self.node.value = self.color.hex  # hex is html-compatible, color.css is not

    def _color_changed_from_dom(self, e):
        self.user_color(self.node.value)

    @event.reaction('disabled')
    def __disabled_changed(self, *events):
        if self.disabled:
            self.node.setAttribute("disabled", "disabled")
        else:
            self.node.removeAttribute("disabled")
