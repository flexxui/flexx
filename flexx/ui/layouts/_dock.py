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
    .p-DockTabPanel {
        padding-right: 2px;
        padding-bottom: 2px;
    }
    
    .p-DockTabPanel > .p-StackedPanel {
        padding: 10px;
        background: white;
        border: 1px solid #C0C0C0;
        border-top: none;
        box-shadow: 1px 1px 2px rgba(0, 0, 0, 0.2);
    }
    
    .p-DockPanel-overlay {
        background: rgba(255, 255, 255, 0.7);
        border: 2px dotted #404040;
    }
    
    .p-DockPanel-overlay.p-mod-root-top,
    .p-DockPanel-overlay.p-mod-root-left,
    .p-DockPanel-overlay.p-mod-root-right,
    .p-DockPanel-overlay.p-mod-root-bottom,
    .p-DockPanel-overlay.p-mod-root-center {
        border-width: 2px;
    }
    """
    
    class JS:
        
        def _init_phosphor_and_node(self):
            self.phosphor = window.phosphor.dockpanel.DockPanel()
            self.node = self.phosphor.node
        
        def _add_child(self, widget):
            self.phosphor.insertRight(widget.phosphor)
            # todo: phosphor allows fine-grained control over where to place the widgets
