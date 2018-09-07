""" TabLayout

A ``StackLayout`` subclass that uses tabs to let the user select a child widget.

Example:

.. UIExample:: 100

    from flexx import app, ui

    class Example(ui.Widget):
        def init(self):
            with ui.TabLayout() as self.t:
                self.a = ui.Widget(title='red', style='background:#a00;')
                self.b = ui.Widget(title='green', style='background:#0a0;')
                self.c = ui.Widget(title='blue', style='background:#00a;')

Also see examples: :ref:`demo.py`.

"""

from pscript import window

from ... import event
from ._stack import StackLayout


class TabLayout(StackLayout):
    """ A StackLayout which provides a tabbar for selecting the current widget.
    The title of each child widget is used for the tab label.
    
    The ``node`` of this widget is a
    `<div> <https://developer.mozilla.org/docs/Web/HTML/Element/div>`_.
    The visible child widget fills the entire area of this element,
    except for a small area at the top where the tab-bar is shown.
    """

    CSS = """

    .flx-TabLayout > .flx-Widget {
        top: 30px;
        margin: 0;
        height: calc(100% - 30px);
        border: 1px solid #ddd;
    }

    .flx-TabLayout > .flx-tabbar {
        box-sizing: border-box;
        position: absolute;
        left: 0;
        right: 0;
        top: 0;
        height: 30px;
        overflow: hidden;
    }

    .flx-tabbar > .flx-tab-item {
        display: inline-block;
        height: 22px;  /* 100% - 8px: 3 margin + 2 borders + 2 padding -1 overlap */
        margin-top: 3px;
        padding: 3px 6px 1px 6px;

        overflow: hidden;
        min-width: 10px;

        -webkit-user-select: none;
        -moz-user-select: none;
        -ms-user-select: none;
        user-select: none;

        background: #ececec;
        border: 1px solid #bbb;
        border-radius: 3px 3px 0px 0px;
        margin-left: -1px;
        transition: background 0.3s;
    }
    .flx-tabbar > .flx-tab-item:first-of-type {
        margin-left: 0;
    }

    .flx-tabbar > .flx-tab-item.flx-current {
        background: #eaecff;
        border-top: 3px solid #7bf;
        margin-top: 0;
    }

    .flx-tabbar > .flx-tab-item:hover {
        background: #eaecff;
    }
    """

    def _create_dom(self):
        outernode = window.document.createElement('div')
        self._tabbar = window.document.createElement('div')
        self._tabbar.classList.add('flx-tabbar')
        self._addEventListener(self._tabbar, 'mousedown',  # also works for touch
                               self._tabbar_click)
        outernode.appendChild(self._tabbar)
        return outernode

    def _render_dom(self):
        nodes = [child.outernode for child in self.children]
        nodes.append(self._tabbar)
        return nodes

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
            node.textContent = widget.title
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

    @event.emitter
    def user_current(self, current):
        """ Event emitted when the user selects a tab. Can be used to distinguish
        user-invoked from programatically-invoked tab changes.
        Has ``old_value`` and ``new_value`` attributes.
        """
        if isinstance(current, (float, int)):
            current = self.children[int(current)]
        d = {'old_value': self.current, 'new_value': current}
        self.set_current(current)
        return d

    def _tabbar_click(self, e):
        index = e.target.index
        if index >= 0:
            self.user_current(index)
