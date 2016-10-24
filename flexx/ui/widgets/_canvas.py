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
    }
    """ 
    
    class JS:
        
        CAPTURE_MOUSE = True
        CAPTURE_WHEEL = False
        
        def _init_phosphor_and_node(self):
            
            self.phosphor = self._create_phosphor_widget('div')
            self.node = window.document.createElement('canvas')
            self.node.id = self.id + '-canvas'
            
            self.phosphor.node.appendChild(self.node)
            # Set position to absolute so that the canvas is not going
            # to be forcing a size on the container div.
            self.node.style.position = 'absolute'
            
            # Disable context menu so we can handle RMB clicks
            # Firefox is particularly stuborn with Shift+RMB, and RMB dbl click
            for ev_name in ('contextmenu', 'click', 'dblclick'):
                window.document.addEventListener(ev_name,
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
                window.document.addEventListener('wheel', wheel_behavior, 0)
        
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
        
        @event.connect('size')
        def _update_canvas_size(self, *events):
            size = events[-1].new_value
            if size[0] or size[1]:
                self.node.width = size[0]
                self.node.height = size[1]
                self.node.style.width = size[0] + 'px'
                self.node.style.height = size[1] + 'px'
