"""
"""

from ... import react
from ...pyscript.stubs import phosphor
from .. import Widget


class CanvasWidget(Widget):
    """ A widget that provides an HTML5 canvas. The canvas is scaled with
    the available space.
    """
    
    class JS:
        
        def _init(self):
            super()._init()
            that = self
            self.node.addEventListener('mousedown', lambda ev: that.mouse_down._set(1), 0)
            self.node.addEventListener('mouseup', lambda ev: that.mouse_down._set(0), 0)
            self.node.addEventListener('mousemove', lambda ev: that.mouse_pos._set((ev.clientX, ev.clientY)), 0)
        
        def _create_node(self):
            self.p = phosphor.createWidget('canvas')
            #self._context = self.node.getContext('2d') -> up to the user
        
        @react.connect('real_size')
        def _update_canvas_size(self, size):
            if size[0] and size[1]:
                self.node.width = size[0]
                self.node.height = size[1]
        
        @react.source
        def mouse_down(v=False):
            """ True when the mouse is currently pressed down.
            """
            return bool(v)
        
        @react.source
        def mouse_pos(pos=(0,0)):
            """ The current position of the mouse inside this widget.
            """
            return float(pos[0]),  float(pos[1])