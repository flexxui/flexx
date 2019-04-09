""" BokehWidget

Show Bokeh plots in Flexx. Example:

.. UIExample:: 300

    import numpy as np
    from bokeh.plotting import figure
    from flexx import app, event, ui

    x = np.linspace(0, 6, 50)

    p1 = figure()
    p1.line(x, np.sin(x))

    p2 = figure()
    p2.line(x, np.cos(x))

    class Example(app.PyComponent):
        def init(self):
            with ui.HSplit():
                ui.BokehWidget.from_plot(p1)
                ui.BokehWidget.from_plot(p2)

Also see examples: :ref:`bokehdemo.py`.

"""


import os

from ... import event, app
from . import Widget


def _load_bokeh(ext):
    bokeh = None
    exec("import bokeh.resources")   # noqa - dont trigger e.g. PyInstaller
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


def make_bokeh_widget(plot, **kwargs):
    Plot = components = None
    exec("from bokeh.models import Plot")  # noqa - dont trigger e.g. PyInstaller
    exec("from from bokeh.embed import components")  # noqa - dont trigger e.g. PyInstaller
    # Set plot prop
    if not isinstance(plot, Plot):
        raise ValueError('plot must be a Bokeh plot object.')
    # The sizing_mode is fixed by default, but that's silly in this context
    if plot.sizing_mode == 'fixed':
        plot.sizing_mode = 'stretch_both'
    # Get components and apply to widget
    script, div = components(plot)
    script = '\n'.join(script.strip().split('\n')[1:-1])
    widget = BokehWidget(**kwargs)
    widget.set_plot_components(
        dict(script=script, div=div, id=plot.ref['id']))
    return widget


class BokehWidget(Widget):
    """ A widget that shows a Bokeh plot object.

    For Bokeh 0.12 and up. The plot's ``sizing_mode`` property is set to
    ``stretch_both`` unless it was set to something other than ``fixed``. Other
    responsive modes are 'scale_width', 'scale_height' and 'scale_both`, which
    all keep aspect ratio while being responsive in a certain direction.

    This widget is, like all widgets, a JsComponent; it lives in the browser,
    while the Bokeh plot is a Python object. Therefore we cannot simply use
    a property to set the plot. Use ``ui.BokehWidget.from_plot(plot)`` to
    instantiate the widget from Python.
    """

    DEFAULT_MIN_SIZE = 100, 100

    CSS = """
    .flx-BokehWidget > .plotdiv {
        overflow: hidden;
    }
    """

    @classmethod
    def from_plot(cls, plot, **kwargs):
        """ Create a BokehWidget using a Bokeh plot.
        """
        return make_bokeh_widget(plot, **kwargs)

    plot = event.Attribute(doc="""The JS-side of the Bokeh plot object.""")

    def _render_dom(self):
        return None

    @event.action
    def set_plot_components(self, d):
        """ Set the plot using its script/html components.
        """
        global window
        # Embed div
        self.node.innerHTML = d.div  # We put trust in d.div
        # "exec" code
        el = window.document.createElement('script')
        el.innerHTML = d.script
        self.node.appendChild(el)
        # Get plot from id in next event-loop iter
        def getplot():
            self._plot = window.Bokeh.index[d.id]
            self.__resize_plot()
        window.setTimeout(getplot, 10)

    @event.reaction('size')
    def __resize_plot(self, *events):
        if self.plot and self.parent:
            if self.plot.resize:
                self.plot.resize()
            else:
                self.plot.model.document.resize()  # older
