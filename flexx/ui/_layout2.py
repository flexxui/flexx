""" High level layout.
"""

from .. import react

from . import Widget
from . import Layout, VBox, HBox


class Panel(Widget):
    """ Widget to collect widgets in a named group. 
    
    It does not provide a layout. In HTML speak, this represents a fieldset.
    
    Example:
    
    .. UIExample:: 100
    
        from flexx import ui
        
        class App(ui.App):
            def init(self):
                with ui.Panel(title='This is a panel'):
                    with ui.VBox():
                        ui.ProgressBar(value=0.2)
                        ui.Button(text='click me')
    
    """
    
    @react.input
    def title(v=''):
        return str(v)
    
    class JS:
        
        def _create_node(self):
            self.node = document.createElement('fieldset')
            self._legend = document.createElement('legend')
            self.node.appendChild(self._legend)
        
        @react.connect('title')
        def _title_changed(self, title):
            self._legend.innerHTML = title



class PlotWidget(Widget):
    """ Widget to show a plot.
    
    This should provide very basic plot functionality, mostly to easily
    demonstrate how plots could be embedded in a Flexx GUI. For real
    plotting, we should have a ``BokehWidget`` and a ``VispyWidget``.
    
    For now, this is mostly a stub...
    
    .. UIExample:: 100
    
        from flexx import ui
        
        class App(ui.App):
            def init(self):
                with ui.HBox():
                    ui.PlotWidget(flex=1)
    
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


class PlotLayout(Layout):
    """ Experimental high-level layout for a plot with widgets on the side.
    
    Example:
    
    .. UIExample:: 300
    
        from flexx import ui
        
        class App(ui.App):
            def init(self):
                layout = ui.PlotLayout()
                layout.add_tools('Edit plot', 
                                 ui.Button(text='do this'),
                                 ui.Button(text='do that'))
                layout.add_tools('Plot info', 
                                 ui.ProgressBar(value='0.3'),
                                 ui.Label(text='The plot aint pretty'))
    
    """
    
    # def __init__(self, *args, **kwargs):
    #     Layout.__init__(self, *args, **kwargs)
    
    def init(self):
        self._box = HBox(parent=self)
        with self._box:
            self._left = VBox(flex=0)
            with VBox(flex=0):
                self._plot = PlotWidget(flex=0)
                Widget(flex=1)
            Widget(flex=1)
        
        # Add stretch element to left vbox
        Widget(flex=1, parent=self._left)
    
    def add_tools(self, name, *args):
        """ Add a set of widgets and collect them in a "tool" panel by
        the given name.
        """
        # Take stretch out
        stretch = self._left.children()[-1]
        stretch.parent(None)
        
        # Add group of widgets
        panel = Panel(title=name, parent=self._left, flex=0)
        vbox = VBox(parent=panel)
        for widget in args:
            widget.parent(vbox)
        
        # Put stretch back in
        stretch.parent(self._left)
