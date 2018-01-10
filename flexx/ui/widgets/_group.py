"""
Simple example:

.. UIExample:: 100
    
    with ui.GroupWidget(title='This is a panel'):
        with ui.VBox():
            ui.ProgressBar(value=0.2)
            ui.Button(text='click me')


Interactive example:

.. UIExample:: 100

    from flexx import app, ui, event
    
    class Example(ui.GroupWidget):
        def init(self):
            self.set_title('A silly panel')
            with ui.VBox():
                ui.ProgressBar(value=0.2)
                self.but = ui.Button(text='click me')
        
        @event.reaction('but.mouse_down')
        def _change_group_title(self, *events):
            self.set_title(self.title + '-')
"""

from ... import event
from ...pyscript import window
from . import Widget


class GroupWidget(Widget):
    """ Widget to collect widgets in a named group. 
    
    It does not provide a layout. This is similar to a QGroupBox or an
    HTML fieldset.
    """
    
    CSS = """
    
    .flx-GroupWidget {
        padding: 5px;
    }
    .flx-GroupWidget > .flx-Layout {
        width: calc(100% - 10px);
        height: calc(100% - 10px);
    }
    
    """
    
    def _create_dom(self):
        node = window.document.createElement('fieldset')
        self._legend = window.document.createElement('legend')
        node.appendChild(self._legend)
        return node
    
    def _render_dom(self):
        nodes = [self._legend]
        for widget in self.children:
            nodes.append(widget.outernode)
        return nodes
    
    @event.reaction('title')
    def _title_changed(self, *events):
        self._legend.innerHTML = self.title
