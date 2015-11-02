"""
"""

from .. import react
from ...pyscript.stubs import phosphor
from . import Widget


class Canvas2D(Widget):
    
    """ A w
    """
    class JS:
        
        def _create_node(self):
            self.p = phosphor.createWidget('canvas')
            self._context = self.node.getContext('2d')
            
            # create tick units
            self._tick_units = []
            for e in range(-10, 10):
                for i in [10, 20, 25, 50]:
                    self._tick_units.append(i*10**e)
        
        @react.connect('real_size')
        def _update_canvas_size(self, size):
            if size[0] and size[1]:
                self.node.width = size[0]
                self.node.height = size[1]
