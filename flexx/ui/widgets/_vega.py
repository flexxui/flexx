"""
The Vega widget is experimental; the embedded plot does not behave well upon
resizing.


Simple example:

.. UIExample:: 200
    
    # Define Vega-lite data. This can also be generated with the Altair library
    spec = {
        "data": {
            "values": [
            {
                "animal": "giraffes",
                "b": 20
            },
            {
                "animal": "orangutans",
                "b": 14
            },
            {
                "animal": "monkeys",
                "b": 23
            }
            ]
        },
        "mark": "bar",
        "encoding": {
            "x": {
            "field": "animal",
            "type": "nominal"
            },
            "y": {
            "field": "b",
            "type": "quantitative"
            },
        }
    }
    
    class Example(ui.VFix):
        def init(self):
            ui.VegaWidget(spec=spec)

"""

from ... import app, event
from . import Widget

# Together about 200KB
app.assets.associate_asset(__name__, "vega.js",
                           "https://cdn.jsdelivr.net/npm/vega@3")
app.assets.associate_asset(__name__, "vega-lite.js",
                           "https://cdn.jsdelivr.net/npm/vega-lite@2")
app.assets.associate_asset(__name__, "vega-embed.js",
                           "https://cdn.jsdelivr.net/npm/vega-embed@3")


class VegaWidget(Widget):
    """ An experimental widget that shows a plot based on Vega or Vega-lite,
    e.g. made with Altair.
    """
    
    spec = event.Property(settable=True, doc="""
        The data (e.g. JSON string) that describes the plot.
        This can e.g. be the output of an Altair plot.
        """)
    
    opt = event.DictProp({"renderer": "canvas", "actions": False}, settable=True, doc="""
        The options dict to style the plot.
        """)
    
    def init(self):
        global document
        self.subnode = document.createElement('div')
        self.node.appendChild(self.subnode)
    
    @event.reaction
    def _init_plot(self):
        global JSON
        global vegaEmbed
        
        spec = self.spec
        opt = self.opt
        
        if isinstance(spec, str):
            spec = JSON.parse(spec)
        self._spec = spec
        
        self._vegaview = None
        vegaEmbed(self.subnode, self._spec, opt).then(self._finalize_init_plot)
    
    def _finalize_init_plot(self, result):
        self._vegaview = result.view
        self._relayout()
    
    @event.reaction
    def _relayout(self):
        # todo: these offsets are arbitrary
        # if you know how to do this better, please help!
        w, h = self.size
        if self._vegaview is not None:
            padding = self._vegaview.padding()
            self._vegaview.width(w - padding.left - padding.right - 150)
            self._vegaview.height(h - padding.top - padding.bottom - 50)
            self._vegaview.run()
