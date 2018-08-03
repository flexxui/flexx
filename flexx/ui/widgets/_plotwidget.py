""" PlotWidget

The plot widget provides rudimentary plotting functionality, mostly to
demonstrate how plots can be embedded in a Flexx GUI. It may be
sufficient for simple cases, but don't expect it to ever support
log-plotting, legends, and other fancy stuff. For real plotting, see
e.g. ``BokehWidget``. There might also be a Plotly widget at some point.


Simple example:

.. UIExample:: 200

    p = ui.PlotWidget(xdata=range(5), ydata=[1,3,4,2,5],
                      line_width=4, line_color='red', marker_color='',
                      minsize=200)

Also see examples: :ref:`sine.py`, :ref:`twente.py`, :ref:`monitor.py`.

"""

from pscript import window

from ... import event
from ._canvas import CanvasWidget


class PlotWidget(CanvasWidget):
    """ Widget to show a plot of x vs y values. Enough for simple
    plotting tasks.
    """

    DEFAULT_MIN_SIZE = 300, 200

    xdata = event.TupleProp((), doc="""
            A list of values for the x-axis. Set via the ``set_data()`` action.
            """)

    ydata = event.TupleProp((), doc="""
            A list of values for the y-axis. Set via the ``set_data()`` action.
            """)

    @event.action
    def set_data(self, xdata, ydata):
        """ Set the xdata and ydata.
        """
        xdata = [float(i) for i in xdata]
        ydata = [float(i) for i in ydata]
        if len(xdata) != len(ydata):
            raise ValueError('xdata and ydata must be of equal length.')
        self._mutate('xdata', xdata)
        self._mutate('ydata', ydata)

    yrange = event.FloatPairProp((0, 0), settable=True, doc="""
        The range for the y-axis. If (0, 0) (default) it is determined
        from the data.
        """)

    line_color = event.ColorProp('#5af', settable=True, doc="""
        The color of the line. Set to the empty string to hide the line.
        """)

    marker_color = event.ColorProp('#5af', settable=True, doc="""
        The color of the marker. Set to the empty string to hide the marker.
        """)

    line_width = event.FloatProp(2, settable=True, doc="""
        The width of the line, in pixels.
        """)

    marker_size = event.FloatProp(6, settable=True, doc="""
        The size of the marker, in pixels.
        """)

    xlabel = event.StringProp('', settable=True, doc="""
        The label to show on the x-axis.
        """)

    ylabel = event.StringProp('', settable=True, doc="""
        The label to show on the y-axis.
        """)

    def init(self):
        super().init()
        self._context = self.node.getContext('2d')

        # create tick units
        self._tick_units = []
        for e in range(-10, 10):
            for i in [10, 20, 25, 50]:
                self._tick_units.append(i*10**e)


    @event.reaction('xdata', 'ydata', 'yrange', 'line_color', 'line_width',
                    'marker_color', 'marker_size', 'xlabel', 'ylabel',
                    'title', 'size')
    def update(self, *events):
        window.requestAnimationFrame(self._update)

    def _update(self):
        xx, yy = self.xdata, self.ydata
        yrange = self.yrange
        lc, lw = self.line_color, self.line_width
        mc, ms = self.marker_color, self.marker_size
        title, xlabel, ylabel = self.title, self.xlabel, self.ylabel

        # Prepare
        ctx = self._context
        w, h = self.node.clientWidth, self.node.clientHeight

        # Get range
        x1, x2 = min(xx), max(xx)
        y1, y2 = min(yy), max(yy)
        #
        if xx:
            x1 -= (x2-x1) * 0.02
            x2 += (x2-x1) * 0.02
        else:
            x1, x2 = 0, 1
        #
        if yrange != (0, 0):
            y1, y2 = yrange
        elif yy:
            y1 -= (y2-y1) * 0.02
            y2 += (y2-y1) * 0.02
        else:
            y1, y2 = 0, 1

        # Convert to screen coordinates
        # 0.5 offset so we land on whole pixels with axis
        lpad = rpad = bpad = tpad = 25.5
        lpad += 30
        if title:
            tpad += 10
        if xlabel:
            bpad += 20
        if ylabel:
            lpad += 20
        scale_x = (w-lpad-rpad) / (x2-x1)
        scale_y = (h-bpad-tpad) / (y2-y1)
        sxx = [lpad + (x-x1)*scale_x for x in xx]
        syy = [bpad + (y-y1)*scale_y for y in yy]

        # Define ticks
        x_ticks = self._get_ticks(scale_x, x1, x2)
        y_ticks = self._get_ticks(scale_y, y1, y2)
        sx_ticks = [lpad + (x-x1)*scale_x for x in x_ticks]
        sy_ticks = [bpad + (y-y1)*scale_y for y in y_ticks]

        ctx.clearRect(0, 0, w, h)

        # Draw inner background
        ctx.fillStyle = 'white'
        ctx.fillRect(lpad, tpad, w-lpad-rpad, h-bpad-tpad)

        # Draw ticks
        ctx.beginPath()
        ctx.lineWidth= 1
        ctx.strokeStyle = "#444"
        for sx in sx_ticks:
            ctx.moveTo(sx, h-bpad)
            ctx.lineTo(sx, h-bpad+5)
        for sy in sy_ticks:
            ctx.moveTo(lpad, h-sy)
            ctx.lineTo(lpad-5, h-sy)
        ctx.stroke()

        # Draw gridlines
        ctx.beginPath()
        ctx.lineWidth= 1
        ctx.setLineDash([2, 2])
        ctx.strokeStyle = "#ccc"
        for sx in sx_ticks:
            ctx.moveTo(sx, h-bpad)
            ctx.lineTo(sx, tpad)
        for sy in sy_ticks:
            ctx.moveTo(lpad, h-sy)
            ctx.lineTo(w-rpad, h-sy)
        ctx.stroke()
        ctx.setLineDash([])

        # Draw tick labels
        ctx.font = '11px verdana'
        ctx.fillStyle = 'black'
        ctx.textAlign = "center"
        ctx.textBaseline = 'top'
        for x, sx in zip(x_ticks, sx_ticks):
            ctx.fillText(x, sx, h-bpad+8)
        ctx.textAlign = "end"
        ctx.textBaseline = 'middle'
        for y, sy in zip(y_ticks, sy_ticks):
            ctx.fillText(y, lpad-8, h-sy)

        # Draw labels
        ctx.textAlign = "center"
        if title:
            ctx.font = '20px verdana'
            ctx.textBaseline = 'top'
            ctx.fillText(title, w/2, 5)
        if xlabel:
            ctx.font = '16px verdana'
            ctx.textBaseline = 'bottom'
            ctx.fillText(xlabel, w/2, h-5)
        if ylabel:
            ctx.save()
            ctx.translate(0, h/2)
            ctx.rotate(-window.Math.PI/2)
            ctx.textBaseline = 'top'
            ctx.fillText(ylabel, 0, 5)
            ctx.restore()

        # Draw axis
        ctx.beginPath()
        ctx.lineWidth= 1
        ctx.strokeStyle = "#444"
        ctx.moveTo(lpad, tpad)
        ctx.lineTo(lpad, h-bpad)
        ctx.lineTo(w-rpad, h-bpad)
        ctx.stroke()

        # Draw line
        if lc.alpha and lw:
            ctx.beginPath()
            ctx.lineWidth= lw
            ctx.strokeStyle = lc.css
            ctx.moveTo(sxx[0], h-syy[0])
            for x, y in zip(sxx, syy):
                ctx.lineTo(x, h-y)
            ctx.stroke()

        # Draw markers
        if mc.alpha and ms:
            ctx.fillStyle = mc.css
            for x, y in zip(sxx, syy):
                ctx.beginPath()
                ctx.arc(x, h-y, ms/2, 0, 2*window.Math.PI)
                ctx.fill()

    def _get_ticks(self, scale, t1, t2, min_tick_dist=40):
        # Get tick unit
        for tick_unit in self._tick_units:
            if tick_unit * scale >= min_tick_dist:
                break
        else:
            return []
        # Calculate tick values
        first_tick = window.Math.ceil(t1 / tick_unit) * tick_unit
        last_tick = window.Math.floor(t2 / tick_unit) * tick_unit
        ticks = []
        t = first_tick
        while t <= last_tick:
            ticks.append(t)
            t += tick_unit
        for i in range(len(ticks)):
            t = ticks[i].toPrecision(4)
            if '.' in t:
                t = t.replace(window.RegExp("[0]+$"), "")
            if t[-1] == '.':
                t += '0'
            ticks[i] = t

        return ticks
