"""
"""

from ... import event
from ...pyscript import window
from .. import Widget

perf_counter = None  # exists in PyScript, time.perf_counter only in Python 3.3+


class CanvasWidget(Widget):
    """ A widget that provides an HTML5 canvas. The canvas is scaled with
    the available space.
    """
    
    CSS = """
    .flx-CanvasWidget {
        min-width: 50px;
        min-height: 50px;
        -webkit-user-select: none;
        -moz-user-select: none;
        -ms-user-select: none;
        user-select: none;
    }
    .flx-CanvasWidget > canvas {
        /* Set position to absolute so that the canvas is not going
         * to be forcing a size on the container div. */
        position: absolute;
    }
    """ 
    
    CAPTURE_MOUSE = 1  # can be useful to set to 2 in many cases
    CAPTURE_WHEEL = False
    
    def _create_dom(self):
        
        outernode = window.document.createElement('div')
        innernode = window.document.createElement('canvas')
        innernode.id = self.id + '-canvas'
        outernode.appendChild(innernode)
        
        # Disable context menu so we can handle RMB clicks
        # Firefox is particularly stuborn with Shift+RMB, and RMB dbl click
        for ev_name in ('contextmenu', 'click', 'dblclick'):
            self._addEventListener(window.document, ev_name,
                                   self._prevent_default_event, 0)
        
        # If the canvas uses the wheel event for something, you'd want to
        # disable browser-scroll when the mouse is over the canvas. But
        # when you scroll down a page and the cursor comes over the canvas
        # because of that, we don't want the canvas to capture too eagerly.
        # This code only captures if there has not been scrolled elsewhere
        # for about half a second.
        def wheel_behavior(e):
            id, t0 = window.flexx._wheel_timestamp
            t1 = perf_counter()
            if (t1 - t0) < 0.5:
                window.flexx._wheel_timestamp = id, t1  # keep scrolling
            else:
                window.flexx._wheel_timestamp = e.target.id, t1  # new scroll
        if not window.flexx._wheel_timestamp:
            window.flexx._wheel_timestamp = 0, ''
            self._addEventListener(window.document, 'wheel', wheel_behavior, 0)
        
        return outernode, innernode
    
    def _prevent_default_event(self, e):
        """ Prevent the default action of an event unless all modifier
        keys (shift, ctrl, alt) are pressed down.
        """
        if e.target is self.node:
            if not (e.altKey is True and e.ctrlKey is True and e.shiftKey is True):
                e.preventDefault()
    
    @event.emitter
    def mouse_wheel(self, e):
        if not self.CAPTURE_WHEEL:
            return super().mouse_wheel(e)  # normal behavior
        elif window.flexx._wheel_timestamp[0] == self.node.id:
            e.preventDefault()
            return super().mouse_wheel(e)
    
    @event.reaction
    def _update_canvas_size(self, *events):
        size = self.size
        if size[0] or size[1]:
            self.node.width = size[0]
            self.node.height = size[1]
            self.node.style.width = size[0] + 'px'
            self.node.style.height = size[1] + 'px'
