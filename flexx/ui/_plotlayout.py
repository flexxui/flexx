""" High level layout.

Example:

.. UIExample:: 300

    from flexx import ui
    
    class Example(ui.Widget):
        def init(self):
            layout = ui.PlotLayout()
            layout.add_tools('Edit plot', 
                                ui.Button(text='do this'),
                                ui.Button(text='do that'))
            layout.add_tools('Plot info', 
                                ui.ProgressBar(value='0.3'),
                                ui.Label(text='The plot aint pretty'))
"""

from .. import react
from . import Widget
from . import Layout, VBox, HBox, Panel, PlotWidget


class PlotLayout(Layout):
    """ Experimental high-level layout for a plot with widgets on the side.
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
