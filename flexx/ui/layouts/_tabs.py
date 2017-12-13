"""
Example:

.. UIExample:: 100
    
    from flexx import app, ui, event
    
    class Example(app.PyComponent):
        def init(self):
            with ui.TabLayout() as self.t:
                self.a = ui.Widget(title='red', style='background:#a00;')
                self.b = ui.Widget(title='green', style='background:#0a0;')
                self.c = ui.Widget(title='blue', style='background:#00a;')
                self.d = ui.Widget(title='unselectable', style='background:#0aa;')
        
        @event.reaction('t.current')
        def cur_tab_changed(self, *events):
            prev = events[0].old_value
            if prev is not None:
                prev.set_title(prev.title.strip(' *'))
            next = events[-1].new_value
            if next is not None:
                next.set_title(next.title + '*')
            # Don't like Cyan
            if next is self.d:
                self.t.set_current(self.a)
"""

from ... import event
from ...pyscript import window, RawJS
from . import Layout, Widget
from ._stack import StackLayout


class TabLayout(StackLayout):
    """ A StackLayout which provides a tabbar for selecting the current widget.
    The title of each child widget is used for the tab label.
    """
    
    CSS = """
    
    .flx-TabLayout > .flx-Widget {
        top: 25px;
        border: 1px solid #777;
    }
    
    .flx-TabLayout > .flx-tabbar {
        box-sizing: border-box;
        position: absolute;
        left: 0;
        right: 0;
        top: 0;
        height: 25px;
        overflow: hidden;
    }
    
    .flx-tabbar > .flx-tab-item {
        display: inline-block;
        height: calc(100% - 6px);  /* 3 margin + 2 borders + 2 padding -1 overlap */
        margin-top: 3px;
        padding: 1px 6px;
        
        overflow: hidden;
        min-width: 10px;

        -webkit-user-select: none;
        -moz-user-select: none;
        -ms-user-select: none;
        user-select: none;
        
        background: #ddd;
        border: 1px solid #777;
        border-radius: 4px 4px 0px 0px;
        margin-left: -1px;
    }
    
    .flx-tabbar > .flx-tab-item.flx-current {
        background: #fff;
        border-bottom: 1px solid white;
        border-top: 3px solid #777;
        margin-top: 0;
    }
    
    .flx-tabbar > .flx-tab-item:hover {
        background: #eee;
    }
    """
    
    def _init_dom(self):
        super()._init_dom()
        self._tabbar = window.document.createElement('div')
        self._tabbar.classList.add('flx-tabbar')
        self._addEventListener(self._tabbar, 'mousedown', self._tabbar_click)
        self.node.appendChild(self._tabbar)
    
    def _update_layout(self, old_children, new_children):
        super()._update_layout(old_children, new_children)
        self.node.appendChild(self._tabbar)
    
    @event.reaction
    def __update_tabs(self):
        children = self.children
        current = self.current
        
        # Add items to tabbar as needed
        while len(self._tabbar.children) < len(children):
            node = window.document.createElement('p')
            node.classList.add('flx-tab-item')
            node.index = len(self._tabbar.children)
            self._tabbar.appendChild(node)
        
        # Remove items from tabbar as needed
        while len(self._tabbar.children) > len(children):
            c = self._tabbar.children[len(self._tabbar.children) - 1]
            self._tabbar.removeChild(c)
        
        # Update titles
        for i in range(len(children)):
            widget = children[i]
            node = self._tabbar.children[i]
            node.innerHTML = widget.title
            if widget is current:
                node.classList.add('flx-current')
            else:
                node.classList.remove('flx-current')
        
        # Update sizes
        self.__checks_sizes()
    
    @event.reaction('size')
    def __checks_sizes(self, *events):
        # Make the tabbar items occupy (nearly) the full width
        nodes = self._tabbar.children
        width = (self.size[0] - 10) / len(nodes) - 2 - 12  # - padding and border
        for i in range(len(nodes)):
            nodes[i].style.width = width + 'px'
    
    def _tabbar_click(self, e):
        index = e.target.index
        if index >= 0:
            self.set_current(index)
