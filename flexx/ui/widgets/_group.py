""" GroupWidget

Visually group a collection of input widgets. Example:

.. UIExample:: 150

    from flexx import app, event, ui

    class Example(ui.GroupWidget):
        def init(self):
            self.set_title('A silly panel')
            with ui.VBox():
                self.progress = ui.ProgressBar(min=0, max=9,
                                               text='Clicked {value} times')
                self.but = ui.Button(text='click me')

        @event.reaction('but.pointer_down')
        def _button_pressed(self, *events):
            self.progress.set_value(self.progress.value + 1)
"""

from ... import event
from . import Widget


class GroupWidget(Widget):
    """ Widget to collect widgets in a named group.
    It does not provide a layout. This is similar to a QGroupBox or an
    HTML fieldset.
    
    The ``node`` of this widget is a
    `<fieldset> <https://developer.mozilla.org/docs/Web/HTML/Element/fieldset>`_. 
    """

    CSS = """

    .flx-GroupWidget {
        margin: 0;
        padding: 5px;
        border: 2px solid #ccc;
        border-radius: 3px;
    }
    .flx-GroupWidget > .flx-Layout {
        width: calc(100% - 10px);
        height: calc(100% - 25px);
    }

    """

    def _create_dom(self):
        global window
        node = window.document.createElement('fieldset')
        self._legend = window.document.createElement('legend')
        node.appendChild(self._legend)
        return node

    def _render_dom(self):
        nodes = [self._legend]
        for widget in self.children:
            nodes.append(widget.outernode)
        return nodes

    def _query_min_max_size(self):
        w1, w2, h1, h2 = super()._query_min_max_size()
        w1 += 10
        h1 += 30
        return w1, w2, h1, h2

    @event.reaction('title')
    def _title_changed(self, *events):
        self._legend.textContent = '\u00A0' + self.title + '\u00A0'
