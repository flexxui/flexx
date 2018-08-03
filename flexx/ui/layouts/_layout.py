""" Layout
"""

from . import Widget


class Layout(Widget):
    """ Abstract class for widgets that layout their child widgets.
    """

    CSS = """

    body {
        margin: 0;
        padding: 0;
    }

    .flx-Layout {
        /* sizing of widgets/layouts inside layout is defined per layout */
        width: 100%;
        height: 100%;
        margin: 0;
        padding: 0;
        border-spacing: 0;
        border: 0;
    }

    """
