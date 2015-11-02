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

from ... import react
from ...pyscript.stubs import phosphor
from . import Layout


# class TabBar(Widget):
#     """ A widget containing tabs.
#     """
#     
#     def _create_node(self):
#         self.p = phosphor.tabs.TabBar()
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
        
        .p-TabBar-content {
            bottom: 1px;
            align-items: flex-end;
            border-bottom: 1px solid #C0C0C0;
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
        
        .p-TabPanel > .p-StackedPanel {
            padding: 10px;
            background: white;
            border: 1px solid #C0C0C0;
            border-top: none;
        }

    """
    
    class JS:
        
        def _create_node(self):
            self.p = phosphor.tabs.TabPanel()
        
        def _add_child(self, widget):
            widget._tab = phosphor.tabs.Tab(widget.title() or '-')
            phosphor.tabs.TabPanel.setTab(widget.p, widget._tab)
            self.p.addWidget(widget.p)
        
        def _remove_child(self, widget):
            if widget._tab:
                del widget._tab
            
        @react.connect('children.*.title')
        def __update_titles(self, *titles):
            for widget in self.children():
                if hasattr(widget, '_tab'):
                    widget._tab.text = widget.title() or '-'
