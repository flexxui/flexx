"""
Example:

.. UIExample:: 200
    
    from flexx import ui
    
    class Example(ui.Widget):
        def init(self):
            with ui.PinboardLayout():
                self.b1 = ui.Button(text='Stuck at (20, 20)', pos=(20, 30), size=(100, 100))
                self.b2 = ui.Button(text='Dynamic at (30%, 30%)', pos=(0.3, 0.3))
                self.b3 = ui.Button(text='Dynamic at (50%, 70%)', pos=(0.5, 0.7))

"""

from ... import react
from . import Widget, Layout


class PinboardLayout(Layout):
    """ A layout that allows positiong child widgets at absolute and
    relative positions without constraining the widgets with respect to
    each-other.
    """
    
    CSS = """
    .flx-pinboardlayout > .flx-widget {
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
        
        @react.connect('children.*.size')
        def __size_changed(self, *sizes):
            for child in self.children():
                size = child.size()[:]
                for i in range(2):
                    if size[i] <= 0 or size is None or size is undefined:
                        size[i] = ''  # Use size defined by CSS
                    elif size[i] > 1:
                        size[i] = size[i] + 'px'
                    else:
                        size[i] = size[i] * 100 + '%'
                child.p.node.style.width = size[0]
                child.p.node.style.height = size[1]
