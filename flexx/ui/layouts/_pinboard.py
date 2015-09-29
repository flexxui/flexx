"""
Example:

.. UIExample:: 200
    
    from flexx import ui
    
    class Example(ui.Widget):
        def init(self):
            with ui.PinboardLayout():
                self.b1 = ui.Button(text='Stuck at (20, 20)', pos=(20, 30), base_size=(100, 100))
                self.b2 = ui.Button(text='Dynamic at (30%, 30%)', pos=(0.3, 0.3))
                self.b3 = ui.Button(text='Dynamic at (50%, 70%)', pos=(0.5, 0.7))

"""

from ... import react
from . import Widget, Layout


class PinboardLayout(Layout):
    """ Unconstrained absolute and relative positiong of child widgets.
    
    The "pos" signal of each child is used to position it. Values
    smaller than 1 are considered relative positions, otherwise the
    position is in pixels. The "base_size" signal is similarly used to
    determine the size of each child. If omitted (i.e. ``(0, 0)``), the
    child widget will have its natural size.
    """
    
    CSS = """
    .flx-PinboardLayout > .flx-Widget {
        position: absolute;
    }
    """
    
    class JS:
        def _create_node(self):
            self.p = phosphor.createWidget('div')
        
        @react.connect('children.*.pos')
        def __pos_changed(self, *poses):
            for child in self.children():
                pos = child.pos()
                child.p.node.style.left = pos[0] + "px" if (pos[0] > 1) else pos[0] * 100 + "%"
                child.p.node.style.top = pos[1] + "px" if (pos[1] > 1) else pos[1] * 100 + "%"
        
        @react.connect('children.*.base_size')
        def __size_changed(self, *sizes):
            for child in self.children():
                size = child.base_size()
                child._set_size('', size[0], size[1])
