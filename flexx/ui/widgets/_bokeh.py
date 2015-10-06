"""
Simple example:

.. UIExample:: 300
    
    import numpy as np
    from bokeh.plotting import figure 
    from flexx import app, ui, react
    
    x = np.linspace(0, 6, 50)
    
    p1 = figure()
    p1.line(x, np.sin(x))
    
    p2 = figure()
    p2.line(x, np.cos(x))
    
    class Example(ui.Widget):
        
        def init(self):
            with ui.BoxPanel():
                ui.BokehWidget(plot=p1)
                ui.BokehWidget(plot=p2)

"""


import os

from ... import react
from . import Widget


class BokehWidget(Widget):
    """ A widget that shows a Bokeh plot object.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Handle client dependencies
        import bokeh
        if not 'bokehjs.min.js' in self.session.get_used_asset_names():
            res = os.path.abspath(os.path.join(bokeh.__file__, '..', 'server', 'static'))
            for x in ('css', 'js'):
                self.session.add_global_asset('bokehjs.min.'+x, os.path.join(res, x, 'bokeh.min.'+x))

    @react.nosync
    @react.input
    def plot(plot):
        """ The Bokeh plot object to display. In JS, this signal
        provides the corresponding backbone model.
        """
        from bokeh.models import PlotObject
        if not isinstance(plot, PlotObject):
            raise ValueError('Plot must be a Bokeh plot object.')
        plot.responsive = True
        return plot
    
    @react.connect('plot')
    def plot_components(plot):
        from bokeh.embed import components
        script, div = components(plot)
        script = '\n'.join(script.split('\n')[1:-1])
        return script, div, plot.ref['id']
    
    class JS:
        
        @react.nosync
        @react.input
        def plot(plot=None):
            return plot
        
        @react.connect('plot_components')
        def __set_plot_components(self, script_div_id):
            script, div, id = script_div_id
            # Embed div
            self.node.innerHTML = div
            # "exec" code
            el = document.createElement('script')
            el.innerHTML = script 
            self.node.appendChild(el)
            #eval(script)
            # Get plot from id in next event-loop iter
            that = this
            def getplot():
                that.plot._set(Bokeh.index[id])
                that.plot().resize()
            window.setTimeout(getplot, 10)
        
        @react.connect('real_size')
        def __resize_plot(self, size):
            if self.plot():
                self.plot().resize()
