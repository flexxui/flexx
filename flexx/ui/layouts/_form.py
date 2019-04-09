""" FormLayout

Layout a series of (input) widgets in a form. Example:

.. UIExample:: 200

    from flexx import ui

    class Example(ui.Widget):
        def init(self):
            with ui.FormLayout():
                self.b1 = ui.LineEdit(title='Name:')
                self.b2 = ui.LineEdit(title="Age:")
                self.b3 = ui.LineEdit(title="Favorite color:")
                ui.Widget(flex=1)  # Spacing

Also see examples: :ref:`themed_form.py`.

"""

from pscript import window

from . import Layout
from .. import create_element


class FormLayout(Layout):
    """ A layout widget that vertically alligns its child widgets in a form.
    A label is placed to the left of each widget (based on the widget's title).

    The ``node`` of this widget is a
    `<div> <https://developer.mozilla.org/docs/Web/HTML/Element/div>`_,
    which lays out it's child widgets and their labels using
    `CSS grid <https://css-tricks.com/snippets/css/complete-guide-grid/>`_.
    """

    CSS = """
    .flx-FormLayout {
        display: grid;
        grid-template-columns: auto 1fr;
        justify-content: stretch;
        align-content: stretch;
        justify-items: stretch;
        align-items: center;

    }
    .flx-FormLayout > .flx-title {
        text-align: right;
        padding-right: 5px;
    }
    """

    def _create_dom(self):
        return window.document.createElement('div')

    def _render_dom(self):
        rows = []
        row_templates = []
        for widget in self.children:
            rows.extend([
                    create_element('div', {'class': 'flx-title'}, widget.title),
                    widget.outernode,
                    ])
            flex = widget.flex[1]
            row_templates.append(flex + "fr" if flex > 0 else "auto")
        self.node.style['grid-template-rows'] = " ".join(row_templates)
        return rows

    def _query_min_max_size(self):
        """ Overload to also take child limits into account.
        """

        # Collect contributions of child widgets
        mima1 = [0, 1e9, 0, 0]
        for child in self.children:
            mima2 = child._size_limits
            mima1[0] = max(mima1[0], mima2[0])
            mima1[1] = min(mima1[1], mima2[1])
            mima1[2] += mima2[2]
            mima1[3] += mima2[3]

        # Dont forget padding and spacing
        extra_padding = 2
        extra_spacing = 2
        for i in range(4):
            mima1[i] += extra_padding
        mima1[2] += extra_spacing
        mima1[3] += extra_spacing

        # Own limits
        mima3 = super()._query_min_max_size()

        # Combine own limits with limits of children
        return [max(mima1[0], mima3[0]),
                min(mima1[1], mima3[1]),
                max(mima1[2], mima3[2]),
                min(mima1[3], mima3[3])]
