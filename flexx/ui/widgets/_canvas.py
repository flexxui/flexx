""" CanvasWidget

The canvas can be used for specialized graphics of many sorts. It can
provide either a WebGL context or a 2d context as in the example below:

.. UIExample:: 100

    from flexx import app, event, ui

    class Example(ui.CanvasWidget):

        def init(self):
            super().init()
            self.ctx = self.node.getContext('2d')
            self.set_capture_mouse(1)
            self._last_pos = (0, 0)

        @event.reaction('pointer_move')
        def on_move(self, *events):
            for ev in events:
                self.ctx.beginPath()
                self.ctx.strokeStyle = '#080'
                self.ctx.lineWidth = 3
                self.ctx.lineCap = 'round'
                self.ctx.moveTo(*self._last_pos)
                self.ctx.lineTo(*ev.pos)
                self.ctx.stroke()
                self._last_pos = ev.pos

        @event.reaction('pointer_down')
        def on_down(self, *events):
            self._last_pos = events[-1].pos

Also see example: :ref:`drawing.py`, :ref:`splines.py`.

"""

from ... import event
from .. import Widget

perf_counter = None  # exists in PScript, time.perf_counter only in Python 3.3+

# todo: make it easy to enable high-res aa


class CanvasWidget(Widget):
    """ A widget that provides an HTML5 canvas. The canvas is scaled with
    the available space. Use ``self.node.getContext('2d')`` or
    ``self.node.getContext('webgl')`` in the ``init()`` method to get
    a contex to perform the actual drawing.
    
    The ``node`` of this widget is a
    `<canvas> <https://developer.mozilla.org/docs/Web/HTML/Element/canvas>`_
    wrapped in a `<div> <https://developer.mozilla.org/docs/Web/HTML/Element/div>`_
    (the ``outernode``) to handle sizing.
    """

    DEFAULT_MIN_SIZE = 50, 50

    CSS = """
    .flx-CanvasWidget {
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

    capture_wheel = event.BoolProp(False, settable=True, doc="""
        Whether the wheel event is "captured", i.e. not propagated to result
        into scrolling of the parent widget (or page). If True, if no scrolling
        must have been performed outside of the widget for about half a second
        in order for the widget to capture scroll events.
        """)

    def _create_dom(self):
        global window

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

    def _create_pointer_event(self, e):
        # In a canvas, prevent browser zooming and the like
        if e.type.startswith('touch'):
            e.preventDefault()
        return super()._create_pointer_event(e)

    @event.emitter
    def pointer_wheel(self, e):
        global window
        if self.capture_wheel <= 0:
            return super().pointer_wheel(e)  # normal behavior
        elif window.flexx._wheel_timestamp[0] == self.node.id:
            e.preventDefault()
            return super().pointer_wheel(e)

    @event.reaction
    def _update_canvas_size(self, *events):
        size = self.size
        if size[0] or size[1]:
            self.node.width = size[0]
            self.node.height = size[1]
            self.node.style.width = size[0] + 'px'
            self.node.style.height = size[1] + 'px'
