""" Layout widgets
"""

from .. import react

from . import Widget


class Layout(Widget):
    """ Abstract class for all layout classes.
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
    
    .flx-layout {
        /* sizing of widgets/layouts inside layout is defined per layout */
        width: 100%;
        height: 100%;
        margin: 0px;
        padding: 0px;
        border-spacing: 0px;
        border: 0px;
    }
    
    """
    
    class JS:
        def _applyBoxStyle(self, e, sty, value):
            for prefix in ['-webkit-', '-ms-', '-moz-', '']:
                e.style[prefix + sty] = value
    
    def swap(self, layout):
        """ Swap this layout with another layout.
        
        Returns the given layout, so that you can do: 
        ``mylayout = mylayout.swap(HBox())``.
        """
        if not isinstance(layout, Layout):
            raise ValueError('Can only swap a layout with another layout.')
        for child in self.children():
            child.parent(layout)
        parent = self.parent()
        self.parent(None)
        layout.parent(parent)
        return layout
        # todo: if parent = None, they are attached to root ...








