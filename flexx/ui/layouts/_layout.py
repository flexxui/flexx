""" Layout widgets
"""

from . import Widget


class Layout(Widget):
    """ Abstract class for widgets that organize their child widgets.
    
    Panel widgets are layouts that do not take the natural size of their
    content into account, making them more efficient and suited for
    high-level layout. Other layouts, like HBox, are more suited for
    laying out content where the natural size is important.
    """
    
    CSS = """
    
    html {
        /* set height, so body can have height, and the first layout too */
        height: 100%;  
    }
    
    body {
        /* Set height so the first layout can fill whole window */
        height: 100%;
        margin: 0px;
    }
    
    .flx-Layout {
        /* sizing of widgets/layouts inside layout is defined per layout */
        width: 100%;
        height: 100%;
        margin: 0px;
        padding: 0px;
        border-spacing: 0px;
        border: 0px;
    }
    
    """
