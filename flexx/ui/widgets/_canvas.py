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
            _mouse_down = lambda ev: that.mouse_down._set(1)
            _mouse_up = lambda ev: that.mouse_down._set(0)
            _mouse_move = lambda ev: that.mouse_pos._set((ev.clientX, ev.clientY))
            self.canvas.addEventListener('mousedown', _mouse_down, 0)
            self.canvas.addEventListener('mouseup', _mouse_up, 0)
            self.canvas.addEventListener('mousemove', _mouse_move, 0)
            # The canvas seems to need a bit of extra help to size at first
            setTimeout(lambda ev=None: that._check_real_size(), 10)
        
        def _create_node(self):
            self.p = phosphor.createWidget('div')
            self.canvas = document.createElement('canvas')
            self.p.node.appendChild(self.canvas)
            # Set position to absolute so that the canvas is not going
            # to be forcing a size on the container div.
            self.canvas.style.position = 'absolute'
        
        @react.connect('real_size')
        def _update_canvas_size(self, size):
            if size[0] and size[1]:
                self.canvas.width = size[0]
                self.canvas.height = size[1]
                self.canvas.style.width = size[0] + 'px'
                self.canvas.style.height = size[1] + 'px'
        
        @react.source
        def mouse_down(v=False):
            """ True when the mouse is currently pressed down.
            """
            return bool(v)
        
        @react.source
        def mouse_pos(self, pos=(0, 0)):
            """ The current position of the mouse inside this widget.
            """
            offset = self.canvas.offsetLeft, self.canvas.offsetTop
            return float(pos[0] - offset[0]), float(pos[1] - offset[1])
