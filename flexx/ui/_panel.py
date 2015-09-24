"""
Simple example:

.. UIExample:: 100
    
    with ui.Panel(title='This is a panel'):
        with ui.VBox():
            ui.ProgressBar(value=0.2)
            ui.Button(text='click me')


Interactive example:

.. UIExample:: 100

    from flexx import app, ui, react
    
    class Example(ui.Panel):
        def init(self):
            self.title('A silly panel')
            with ui.VBox():
                ui.ProgressBar(value=0.2)
                self.but = ui.Button(text='click me')
        
        class JS:
            @react.connect('but.mouse_down')
            def _change_panel_title(self, down):
                if down:
                    self.title(self.title() + '-')

"""

from .. import react
from . import Widget


class Panel(Widget):
    """ Widget to collect widgets in a named group. 
    
    It does not provide a layout. In HTML speak, this represents a fieldset.
    """
    
    @react.input
    def title(v=''):
        return str(v)
    
    class JS:
        
        def _create_node(self):
            self.p = phosphor.createWidget('fieldset')
            self._legend = document.createElement('legend')
            self.p.node.appendChild(self._legend)
        
        @react.connect('title')
        def _title_changed(self, title):
            self._legend.innerHTML = title
