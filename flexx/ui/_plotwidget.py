"""
.. UIExample:: 100

    from flexx import ui
    
    class Example(ui.Widget):
        def init(self):
            with ui.HBox():
                ui.PlotWidget(flex=1)

"""


from .. import react
from . import Widget


class PlotWidget(Widget):
    """ Widget to show a plot.
    
    This should provide very basic plot functionality, mostly to easily
    demonstrate how plots could be embedded in a Flexx GUI. For real
    plotting, we should have a ``BokehWidget`` and a ``VispyWidget``.
    
    For now, this is mostly a stub...
    """
    
    class JS:
        def _create_node(self):
            self.node = document.createElement('canvas')
            self._context = ctx = self.node.getContext('2d')
            
            ctx.beginPath()
            ctx.lineWidth= '3'
            ctx.strokeStyle = "blue" 
            ctx.moveTo(10, 60)
            for i in range(40):
                ctx.lineTo(10 + i * 10, 
                        60 + 40 * Math.sin(0.5*i))
            ctx.stroke()
            
            ctx.fillText("Imagine that this is a fancy plot ...", 10, 10)
