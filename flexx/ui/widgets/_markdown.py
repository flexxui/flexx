"""

Simple example:

.. UIExample:: 200

    def init(self):
        content = "# Welcome\n\n" \
            "Hello.  Welcome to my **website**. This is an example of a widget container for markdown content. " \
            "The content can be text or a link.\n\n"
        ui.Markdown(content=content, style='background:#EAECFF;height:60%;')

Also see example: :ref:`ui_usage/markdown.py`.

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
