"""
The splitter layout classes provide a mechanism to horizontally
or vertically stack child widgets, where the available space can be
manually specified by the user.

Example:

.. UIExample:: 200
    
    from flexx import ui
    
    class Example(ui.Widget):
        def init(self):
            with ui.SplitPanel(orientation='h'):
                ui.Label(text='red', style='background:#f77;')
                with ui.SplitPanel(orientation='v'):
                    ui.Label(text='green', style='background:#7f7;')
                    ui.Label(text='blue', style='background:#77f')
                    ui.Label(text='purple', style='background:#f7f;')
"""

from ... import event
from ...pyscript import RawJS
from . import Layout


_phosphor_splitpanel = RawJS("flexx.require('phosphor/lib/ui/splitpanel')")


class SplitPanel(Layout):
    """ Layout to split space for widgets horizontally or vertically.
    
    The Splitter layout divides the available space among its child
    widgets in a similar way that Box does, except that the
    user can divide the space by dragging the divider in between the
    widgets.
    """
    
    _DEFAULT_ORIENTATION = 'h'
    
    class Both:
    
        @event.prop
        def spacing(self, v=5):
            """ The space between two child elements (in pixels)"""
            return float(v)
        
        @event.prop
        def orientation(self, v=None):
            """ The orientation of the child widgets. 'h' or 'v'. Default
            horizontal.
            """
            if v is None:
                v = self._DEFAULT_ORIENTATION
            if isinstance(v, str):
                v = v.lower()
            v = {'horizontal': 'h', 'vertical': 'v', 0: 'h', 1: 'v'}.get(v, v)
            if v not in ('h', 'v'):
                raise ValueError('%s.orientation got unknown value %r' % (self.id, v))
            return v
    
    class JS:
        
        _DEFAULT_ORIENTATION = 'h'
        
        def _init_phosphor_and_node(self):
            self.phosphor = _phosphor_splitpanel.SplitPanel()
            self.node = self.phosphor.node
            window.setTimeout(0.01, self._set_flexes)  # Phosphor seems to need one iter to "settle"
        
        @event.connect('spacing')
        def __spacing_changed(self, *events):
            self.phosphor.spacing = self.spacing
        
        @event.connect('orientation', 'children', 'children*.flex')
        def _set_flexes(self, *events):
            ori = self.orientation
            i = 0 if ori in (0, 'h', 'hr') else 1
            # Set orientation
            if ori == 0 or ori == 'h':
                self.phosphor.orientation = 'horizontal'
            elif ori == 1 or ori == 'v':
                self.phosphor.orientation = 'vertical'
            else:
                raise ValueError('Invalid splitter orientation: ' + ori)
            # Set sizes
            flexes = []
            for widget in self.children:
                flex = widget.flex[i]
                flexes.append(flex + 0.1)
            self.phosphor.setRelativeSizes(flexes)
