"""
The dockpanel layoujt widget.
"""

from .. import react
from . import Widget, Layout


class DockLayout(Layout):
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
        
        .p-TabBar {
            min-height: 24px;
        }
        
        .p-TabBar-content {
            bottom: 1px;
            align-items: flex-end;
        }
        
        .p-TabBar-content > .p-Tab {
            flex-basis: 125px;
            max-height: 21px;
            min-width: 35px;
            margin-left: -1px;
            border: 1px solid #C0C0C0;
            border-bottom: none;
            padding: 0px 10px;
            background: #E5E5E5;
            font: 12px Helvetica, Arial, sans-serif;
        }
        
        .p-TabBar-content > .p-Tab.p-mod-first {
            margin-left: 0;
        }
        
        .p-TabBar-content > .p-Tab.p-mod-selected {
            min-height: 24px;
            background: white;
            transform: translateY(1px);
        }
        
        .p-TabBar-content > .p-Tab:hover:not(.p-mod-selected) {
            background: #F0F0F0;
        }
        
        .p-TabBar-content > .p-Tab > span {
            line-height: 21px;
        }
        
        .p-TabBar-footer {
            display: block;
            height: 1px;
            background: #C0C0C0;
        }
        
        .p-Tab.p-mod-closable > .p-Tab-close-icon {
            margin-left: 4px;
        }
        
        .p-Tab.p-mod-closable > .p-Tab-close-icon:before {
            content: '\f00d';
            font-family: FontAwesome;
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
            
            if not widget.p:
                pwidget = phosphor.widget.Widget()
                pwidget.node.appendChild(widget.node)
                widget._pindex = self.p.childCount
            else:
                pwidget = widget.p
            
            tab = phosphor.tabs.Tab(widget.title())
            widget._tab = tab
            phosphor.dockpanel.DockPanel.setTab(pwidget, tab)
            #self.p.tabProperty.set(pwidget, tab)
            
            self.p.addWidget(pwidget)
        
        def _remove_child(self, widget):
            if widget._tab:
                del widget._tab
            
        @react.connect('children.*.title')
        def __update_titles(self, *titles):
            for widget in self.children():
                if hasattr(widget, '_tab'):
                    widget._tab.text = widget.title()
