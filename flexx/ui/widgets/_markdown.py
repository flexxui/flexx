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

app.assets.associate_asset(__name__, 'https://cdnjs.cloudflare.com/ajax/libs/showdown/1.9.1/showdown.min.js')


class Markdown(Widget):
    """ A widget that shows a rendered Markdown content.
    """
    CSS = """

    .flx-Markdown {
        height: min(100vh,100%);
        overflow-y: auto;
    }
    """

    content = event.StringProp(settable=True, doc="""
        The markdown content to be rendered
        """)

    @event.reaction
    def __content_change(self):
        global showdown
        conv = showdown.Converter();
        self.node.innerHTML = conv.makeHtml(self.content);
