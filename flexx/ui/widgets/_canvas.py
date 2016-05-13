"""
"""

from ... import event
from ...pyscript import window
from .. import Widget


class CanvasWidget(Widget):
    """ A widget that provides an HTML5 canvas. The canvas is scaled with
    the available space.
    """
    
    CSS = """
    .flx-CanvasWidget {
        min-width: 50px;
        min-height: 50px;
    }
    """ 
    
    class JS:
        
        CAPTURE_MOUSE = True
        
        def _init_phosphor_and_node(self):
            
            self.phosphor = window.phosphor.createWidget('div')
            self.node = window.document.createElement('canvas')
            
            self.phosphor.node.appendChild(self.node)
            # Set position to absolute so that the canvas is not going
            # to be forcing a size on the container div.
            self.node.style.position = 'absolute'
        
        @event.connect('size')
        def _update_canvas_size(self, *events):
            size = events[-1].new_value
            if size[0] or size[1]:
                self.node.width = size[0]
                self.node.height = size[1]
                self.node.style.width = size[0] + 'px'
                self.node.style.height = size[1] + 'px'
