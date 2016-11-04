"""
Example:

.. UIExample:: 100
    
    from flexx import app, ui, event
    
    class Example(ui.Widget):
        def init(self):
            with ui.TabPanel() as self.t:
                self.a = ui.Widget(title='red', style='background:#a00;')
                self.b = ui.Widget(title='green', style='background:#0a0;')
                self.c = ui.Widget(title='blue', style='background:#00a;')
                self.d = ui.Widget(title='cyan', style='background:#0aa;')
    
        class JS:
        
            @event.connect('t.current')
            def cur_tab_changed(self, *events):
                prev = events[0].old_value
                if prev is not None:
                    prev.title = prev.title.strip(' *')
                next = events[-1].new_value
                if next is not None:
                    next.title = next.title + '*'
                # Don't like Cyan
                if next is self.d:
                    self.t.current = self.a
"""

from ... import event
from ...pyscript import window
from . import Layout, Widget


# class TabBar(Widget):
#     """ A widget containing tabs.
#     """
#     
#     def _init_phosphor_and_node(self):
#         self.phosphor = window.phosphor.ui.tabbar.TabBar()
#         self.node = self.phosphor.node
# 
#     def _add_child(self, widget):
#         raise ValueError('A TabBar cannot have children.')


class TabPanel(Layout):
    """ A panel which provides a tabbed layout for child widgets.
    
    The title of each child widget is used for the tab label.
    
    todo: this needs a way to get/set the current order of the widgets.
    """
    
    # This CSS is taken from the Phosphor example, but we "prefix" it, so that
    # it does not screw up style of other Phosphor stuff on the same page.
    CSS = """
        .flx-Widget .p-TabBar {
            min-height: 24px;
            max-height: 24px;
        }
        
        .flx-Widget .p-TabBar-content {
            min-width: 0;
            min-height: 0;
            align-items: flex-end;
            border-bottom: 1px solid #C0C0C0;
        }
        
        .flx-Widget .p-TabBar-tab {
            padding: 0px 10px;
            background: #E5E5E5;
            border: 1px solid #C0C0C0;
            border-bottom: none;
            font: 12px Helvetica, Arial, sans-serif;
            flex: 0 1 125px;
            min-height: 20px;
            max-height: 20px;
            min-width: 35px;
            margin-left: -1px;
            line-height: 20px;
        }
        
        .flx-Widget .p-TabBar-tab.p-mod-current {
            background: white;
        }
        
        .flx-Widget .p-TabBar-tab:hover:not(.p-mod-current) {
            background: #F0F0F0;
        }
        
        .flx-Widget .p-TabBar-tab:first-child {
            margin-left: 0;
        }
        
        .flx-Widget .p-TabBar-tab.p-mod-current {
            min-height: 23px;
            max-height: 23px;
            transform: translateY(1px);
        }
        
        .flx-Widget .p-TabBar-tabIcon,
        .flx-Widget .p-TabBar-tabLabel,
        .flx-Widget .p-TabBar-tabCloseIcon {
            display: inline-block;
        }
        
        .flx-Widget .p-TabBar-tab.p-mod-closable > .p-TabBar-tabCloseIcon {
            margin-left: 4px;
        }
        
        .flx-Widget .p-TabBar-tab.p-mod-closable > .p-TabBar-tabCloseIcon:before {
            content: '\f00d';
            font-family: FontAwesome;
        }
        
        .flx-Widget .p-TabBar-tab.p-mod-drag-image {
            min-height: 23px;
            max-height: 23px;
            min-width: 125px;
            border: none;
            box-shadow: 1px 1px 2px rgba(0, 0, 0, 0.3);
            transform: translateX(-40%) translateY(-58%);
        }
    """
    
    class Both:
        
        @event.prop
        def current(self, v=None):
            """ The currently shown widget.
            """
            if not (v is None or isinstance(v, Widget)):
                raise ValueError("%s.current should be a Widget, not %r" % (self.id, v))
            return v
    
    class JS:
        
        def _init_phosphor_and_node(self):
            self.phosphor = window.phosphor.ui.tabpanel.TabPanel()
            self.node = self.phosphor.node
            
            def _phosphor_changes_current(v, info):
                if info.currentWidget:
                    self.current = window.flexx.instances[info.currentWidget.id]
            self.phosphor.currentChanged.connect(_phosphor_changes_current)
        
        @event.connect('current')
        def __current_changed_via_prop(self, *events):
            w = events[-1].new_value
            if w is None:
                self.phosphor.currentWidget = None
            else:
                self.phosphor.currentWidget = w.phosphor
