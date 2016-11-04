"""

Example:

.. UIExample:: 250
    
    from flexx import ui
    
    class Example(ui.Widget):
        def init(self):
            with ui.DockPanel():
                ui.Widget(style='background:#a00;', title='red')
                ui.Widget(style='background:#0a0;', title='green')
                ui.Widget(style='background:#00a;', title='blue')
                ui.Widget(style='background:#aa0;', title='yellow')
                ui.Widget(style='background:#a0a;', title='purple')
                ui.Widget(style='background:#0aa;', title='cyan')

"""

from ...pyscript import window
from . import Layout


class DockPanel(Layout):
    """ A layout that displays its children as dockable widgets. 
    
    This is a high level layout allowing the user to layout the child
    widgets as he/she likes. The title of each child is used for its
    corresponding tab label.
    
    NOTE: this class needs some work to allow setting and getting the
    positioning of the child widgets ...
    """
    
    CSS = """
    .flx-Widget .p-DockPanel-overlay {
        background: rgba(255, 255, 255, 0.6);
        border: 2px solid rgba(0, 0, 0, 0.6);;
        transition-property: top, left, right, bottom;
        transition-duration: 100ms;
        transition-timing-function: ease;
    }
    """
    
    # todo: properties for spacing (self.phosphor.spacing)
    
    class JS:
        
        def _init_phosphor_and_node(self):
            self.phosphor = window.phosphor.ui.dockpanel.DockPanel()
            self.node = self.phosphor.node
        
        def _add_child(self, widget):
            self.phosphor.addWidget(widget.phosphor)
            # todo: phosphor allows fine-grained control over where to place the widgets
