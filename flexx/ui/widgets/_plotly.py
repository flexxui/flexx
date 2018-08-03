"""

Simple example:

.. UIExample:: 200

    # Define data. This can also be generated with the plotly Python library
    data = [{'type': 'bar',
             'x': ['giraffes', 'orangutans', 'monkeys'],
             'y': [20, 14, 23]}]

    # Show
    p = ui.PlotlyWidget(data=data)

Also see examples: :ref:`plotly_gdp.py`.

"""

from ... import app, event
from . import Widget

app.assets.associate_asset(__name__, 'https://cdn.plot.ly/plotly-latest.min.js')


class PlotlyWidget(Widget):
    """ A widget that shows a Plotly visualization.
    """

    data = event.ListProp(settable=True, doc="""
        The data (list of dicts) that describes the plot.
        This can e.g. be the output of the Python plotly API call.
        """)

    layout = event.DictProp(settable=True, doc="""
        The layout dict to style the plot.
        """)

    config = event.DictProp(settable=True, doc="""
        The config for the plot.
        """)

    @event.reaction
    def __relayout(self):
        global Plotly
        w, h = self.size
        if len(self.node.children) > 0:
            Plotly.relayout(self.node, dict(width=w, height=h))

    @event.reaction
    def _init_plot(self):
        # https://plot.ly/javascript/plotlyjs-function-reference/#plotlynewplot
        # Overwrites an existing plot
        global Plotly
        Plotly.newPlot(self.node, self.data, self.layout, self.config)
