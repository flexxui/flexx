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
from ...pyscript import window, RawJS
from . import Layout, Widget


#_phosphor_tabbar = RawJS("flexx.require('phosphor/lib/ui/tabbar')")
_phosphor_tabpanel = RawJS("flexx.require('phosphor/lib/ui/tabpanel')")


# class TabBar(Widget):
#     """ A widget containing tabs.
#     """
#     
#     def _init_phosphor_and_node(self):
#         self.phosphor = _phosphor_tabbar.TabBar()
#         self.node = self.phosphor.node
# 
#     def _add_child(self, widget):
#         raise ValueError('A TabBar cannot have children.')


class TabPanel(Layout):
    """ A panel which provides a tabbed layout for child widgets.
    
    The title of each child widget is used for the tab label.
    
    todo: this needs a way to get/set the current order of the widgets.
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
            self.phosphor = _phosphor_tabpanel.TabPanel()
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
