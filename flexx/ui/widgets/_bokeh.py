"""
Simple example:

.. UIExample:: 300
    
    import numpy as np
    from bokeh.plotting import figure 
    from flexx import app, ui, event
    
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

from ... import event, app
from ...pyscript.stubs import window, Bokeh
from . import Widget


def _load_bokeh(ext):
    import bokeh.resources
    dev = os.environ.get('BOKEH_RESOURCES', '') == 'relative-dev'
    res = bokeh.resources.bokehjsdir()
    if dev:
        res = os.path.abspath(os.path.join(bokeh.__file__,
                                            '..', '..', 'bokehjs', 'build'))
    modname = 'bokeh' if dev else 'bokeh.min'
    filename = os.path.join(res, ext, modname + '.' + ext)
    return open(filename, 'rb').read().decode()

def _load_bokeh_js():
    return _load_bokeh('js')

def _load_bokeh_css():
    return _load_bokeh('css')

# Associate Bokeh asset, but in a "lazy" way, so that we don't attempt to
# import bokeh until the user actually instantiates a BokehWidget.
app.assets.associate_asset(__name__, 'bokeh.js', _load_bokeh_js)
app.assets.associate_asset(__name__, 'bokeh.css', _load_bokeh_css)


class BokehWidget(Widget):
    """ A widget that shows a Bokeh plot object.
    
    For Bokeh 0.12 and up. The plot's ``sizing_mode`` property is set to
    ``stretch_both`` unless it was set to something other than ``fixed``. Other
    responsive modes are 'scale_width', 'scale_height' and 'scale_both`, which
    all keep aspect ratio while being responsive in a certain direction.
    """
    
    CSS = """
    .flx-BokehWidget > .plotdiv {
        overflow: hidden;
    }
    """
    
    @event.prop
    def plot(self, plot=None):
        """ The Bokeh plot object to display. In JS, this prop
        provides the corresponding backbone model.
        """
        try:
            from bokeh.models import Plot
        except ImportError:
            from bokeh.models import PlotObject as Plot
        if plot is None:
            return None
        if not isinstance(plot, Plot):
            raise ValueError('%s.plot must be a Bokeh plot object.' % self.id)
        # The sizing_mode is fixed by default, but that's silly in this context
        if plot.sizing_mode == 'fixed':
            plot.sizing_mode = 'stretch_both'
        self._plot_components(plot)
        return plot
    
    @event.emitter
    def _plot_components(self, plot):
        from bokeh.embed import components
        script, div = components(plot)
        script = '\n'.join(script.strip().split('\n')[1:-1])
        return dict(script=script, div=div, id=plot.ref['id'])
    
    class JS:
        
        @event.prop
        def plot(self, plot=None):
            return plot
        
        @event.connect('_plot_components')
        def __set_plot_components(self, *events):
            ev = events[-1]
            # Embed div
            self.node.innerHTML = ev.div
            # "exec" code
            el = window.document.createElement('script')
            el.innerHTML = ev.script 
            self.node.appendChild(el)
            #eval(script)
            # Get plot from id in next event-loop iter
            def getplot():
                self.plot = Bokeh.index[ev.id]
                self.plot.model.document.resize()
                #self.real_size._set(self.real_size) ???
            window.setTimeout(getplot, 10)
        
        @event.connect('size')
        def __resize_plot(self, *events):
            if self.plot and self.parent:
                if self.plot.resize_width_height:
                    # Bokeh <= 0.11
                    cstyle = window.getComputedStyle(self.parent.node)
                    use_x = cstyle['overflow-x'] not in ('auto', 'scroll')
                    use_y = cstyle['overflow-y'] not in ('auto', 'scroll')
                    self.plot.resize_width_height(use_x, use_y)
                else:
                    self.plot.model.document.resize()
