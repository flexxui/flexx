"""
The dockpanel layoujt widget.
"""

from .. import react
from . import Widget, Layout


class DockPanel(Layout):
    """
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
        
        .p-DockTabPanel-overlay {
            background: rgba(255, 255, 255, 0.6);
            border: 1px solid rgba(0, 0, 0, 0.6);
        }
        
        .p-Tab.p-mod-docking {
            font: 12px Helvetica, Arial, sans-serif;
            height: 24px;
            width: 125px;
            padding: 0px 10px;
            background: white;
            box-shadow: 1px 1px 2px rgba(0, 0, 0, 0.3);
            transform: translateX(-50px) translateY(-14px);
        }
        
        .p-Tab.p-mod-docking > span {
            line-height: 21px;
        }
    """
    
    class JS:
        
        def _create_node(self):
            self.p = phosphor.dockpanel.DockPanel()
        
        def _add_child(self, widget):
            widget._tab = phosphor.tabs.Tab(widget.title())
            phosphor.dockpanel.DockPanel.setTab(widget.p, widget._tab)
            self.p.addWidget(widget.p)
            
        def _remove_child(self, widget):
            if widget._tab:
                del widget._tab
            
        @react.connect('children.*.title')
        def __update_titles(self, *titles):
            for widget in self.children():
                if hasattr(widget, '_tab'):
                    widget._tab.text = widget.title()
