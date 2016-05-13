"""
Example:

.. UIExample:: 100
    
    from flexx import app, ui
    
    class Example(ui.Widget):
        def init(self):
            with ui.TabPanel():
                self.a = ui.Widget(title='red', style='background:#a00;')
                self.b = ui.Widget(title='green', style='background:#0a0;')
                self.c = ui.Widget(title='blue', style='background:#00a;')
"""

from ...pyscript import window
from . import Layout


# class TabBar(Widget):
#     """ A widget containing tabs.
#     """
#     
#     def _init_phosphor_and_node(self):
#         self.phosphor = window.phosphor.tabs.TabBar()
#         self.node = self.phosphor.node
# 
#     def _add_child(self, widget):
#         raise ValueError('A TabBar cannot have children.')


class TabPanel(Layout):
    """ A panel which provides a tabbed layout for child widgets.
    
    The title of each child widget is used for the tab label.
    
    todo: this needs a way to get/set the current order of the widgets.
    """
    
    CSS = """
        .p-TabBar {
            min-height: 24px;
        }
        
        .p-TabBar-body {
            bottom: 1px;
            border-bottom: 1px solid #C0C0C0;
        }
        
        .p-TabBar-footer {
            display: block;
            height: 1px;
            background: #C0C0C0;
        }
        
        .p-TabBar-content {
            align-items: flex-end;
        }
        
        .p-TabBar-tab {
            flex-basis: 125px;
            max-height: 21px;
            margin-left: -1px;
            border: 1px solid #C0C0C0;
            border-bottom: none;
            padding: 0px 10px;
            background: #E5E5E5;
            font: 12px Helvetica, Arial, sans-serif;
        }
        
        .p-TabBar-tab:first-child {
            margin-left: 2px;
        }
        
        .p-TabBar-tab.p-mod-current {
            min-height: 24px;
            background: white;
            transform: translateY(1px);
        }
        
        .p-TabBar-tab:hover:not(.p-mod-current) {
            background: #F0F0F0;
        }
        
        .p-TabBar-tab-icon,
        .p-TabBar-tab-text,
        .p-TabBar-tab-close {
            line-height: 21px;
        }
        
        .p-TabPanel > .p-StackedPanel {
            padding: 10px;
            background: white;
            border: 1px solid #C0C0C0;
            border-top: none;
        }
        
        .p-TabBar-tab.p-mod-closable > .p-TabBar-tab-close {
            margin-left: 4px;
        }
        
        .p-TabBar-tab.p-mod-closable > .p-TabBar-tab-close:before {
            content: '\f00d';
            font-family: FontAwesome;
        }
    """
    
    class JS:
        
        def _init_phosphor_and_node(self):
            self.phosphor = window.phosphor.tabs.TabPanel()
            self.node = self.phosphor.node
