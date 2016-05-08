""" Experimental high level layout for dashboards. Do not rely on this.

Example:

.. UIExample:: 300

    from flexx import app, ui, event
    
    class Example(ui.Widget):
        def init(self):
            self.layout = ui.PlotLayout()
            self.slider1 = ui.Slider(min=1, max=2, value=1)
            self.slider2 = ui.Slider(min=3, max=10, value=3)
            self.progress = ui.ProgressBar(max=100, value=0)
            self.layout.add_tools('Edit plot', 
                                ui.Label(text='exponent'), self.slider1,
                                ui.Label(text='numel'), self.slider2,
                                )
            self.layout.add_tools('Plot info', ui.Label(text='Maximum'), self.progress)
        
        class JS:
            
            @event.connect('slider1.value', 'slider2.value')
            def __update_plot(self, *events):
                e, n = self.slider1.value, self.slider2.value
                xx = range(n+1)
                self.layout._plot.xdata = xx
                self.layout._plot.ydata = [x**e for x in xx]
            
            @event.connect('layout._plot.ydata')
            def __update_max(self, *events):
                yy = events[-1].new_value
                if yy:
                    self.progress.value = max(yy)

"""

from . import Widget
from . import Layout, VBox, HBox, GroupWidget, PlotWidget


class PlotLayout(Layout):
    """ Experimental high-level layout for a plot with widgets on the side.
    """
    
    def init(self):
        self._box = HBox(parent=self)
        with self._box:
            with VBox():
                self._left = VBox(flex=0)
            with VBox(flex=0):
                #self._plot = PlotWidget(flex=1)
                self._plot = PlotWidget(flex=0, 
                                        style='min-width:640px; min-height:480px;')
                Widget(flex=1)
            Widget(flex=1)
        
        # Add stretch element to left vbox
        Widget(flex=1, parent=self._left)
    
    def add_tools(self, name, *args):
        """ Add a set of widgets and collect them in a "tool" GroupWidget by
        the given name.
        """
        
        # Add group of widgets
        panel = GroupWidget(title=name, parent=self._left, flex=0)
        vbox = VBox(parent=panel)
        for widget in args:
            widget.parent = vbox
