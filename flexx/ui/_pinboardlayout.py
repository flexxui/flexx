"""
Example:

.. UIExample:: 200
    
    from flexx import ui
    
    class Example(ui.Widget):
        def init(self):
            with ui.PinboardLayout():
                self.b1 = ui.Button(text='Stuck at (20, 20)', pos=(20, 30))
                self.b2 = ui.Button(text='Dynamic at (30%, 30%)', pos=(0.3, 0.3))
                self.b3 = ui.Button(text='Dynamic at (50%, 70%)', pos=(0.5, 0.7))

"""

from .. import react
from . import Widget, Layout

class PinboardLayout(Layout):
    """ A layout that allows positiong child widgets at absolute and
    relative positions without constraining the widgets with respect to
    each-other.
    """
    
    CSS = """
    .flx-pinboardlayout-xxxxx {
        position: relative;
    }
    .flx-pinboardlayout > .flx-widget {
        position: absolute;
    }
    """
    
    class JS:
        def _create_node(self):
            this.node = document.createElement('div')