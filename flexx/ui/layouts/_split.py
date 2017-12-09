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
from ...pyscript import RawJS, window
from . import Layout


# _phosphor_splitpanel = RawJS("flexx.require('phosphor/lib/ui/splitpanel')")


class SplitPanel(Layout):
    """ Layout to split space for widgets horizontally or vertically.
    
    The Splitter layout divides the available space among its child
    widgets in a similar way that Box does, except that the
    user can divide the space by dragging the divider in between the
    widgets.
    """
    
    CSS = """
    
    .flx-SplitPanel > .flx-Widget {
        position: absolute;
    }
    
    .flx-split-sep.flx-horizontal {
        cursor: ew-resize;  
    }
    .flx-split-sep.flx-vertical {
        cursor: ns-resize;
    }
    .flx-split-sep {
        z-index: 2;
        position: absolute;
        -webkit-user-select: none;
        -moz-user-select: none;
        -ms-user-select: none;
        user-select: none;
        box-sizing: border-box;
        /*background: rgba(0, 0, 0, 0);*/
        background: #fff;
    }
    .flx-split-sep:hover {
        background: #ddd;
        /*box-shadow: 0 0 8px rgba(0, 0, 0, 0.25);*/
    }
    """
    
    _DEFAULT_ORIENTATION = 'h'
    
    spacing = event.FloatProp(5, settable=True, doc="""
        The space between two child elements (in pixels)
        """)
    
    # todo: implement setter, or implement OrientationProp to share with box
    orientation = event.StringProp('h', settable=True, doc="""
        The orientation of the child widgets. 'h' or 'v'. Default horizontal.
        """)
    
    ## Actions
    
    @event.action
    def set_from_flex_values(self):
        """ Set the divider positions corresponding to the children's flex values.
        """
        
        # Collect flexes
        sizes = []
        dim = 0 if 'h' in self.orientation else 1
        for widget in self.children:
            sizes.append(widget.flex[dim])
        
        # Normalize size, so that total is one
        total_size = sum(sizes)
        if total_size == 0:
            sizes = [1/len(sizes) for j in sizes]
        else:
            sizes = [j/total_size for j in sizes]
        # todo: pyscript bug: if I use i here, it takes on value set above (0)
        
        # Turn sizes into positions
        positions = []
        pos = 0
        for i in range(len(sizes) - 1):
            pos = pos + sizes[i]
            positions.append(pos)
        
        # Apply
        self.set_divider_positions(*positions)
    
    @event.action
    def set_divider_positions(self, *positions):
        """ Set relative divider posisions (values between 0 and 1).
        """
        print(positions)
        total_size, available_size = self._get_available_size()
        
        positions = [max(0, min(1, pos)) * available_size for pos in positions]
        self._set_absolute_divider_positions(*positions)
    
    ## Reactions and hooks
    
    def _init_dom(self):
        self.outernode = window.document.createElement('div')
        self.node = self.outernode
        
        self._seps = []
        self._dragging = None
        
        # window.setTimeout(0.01, self._set_flexes)
    
    def _update_layout(self, old_children, new_children):
        """ Can be overloaded in (Layout) subclasses.
        """
        for c in self.outernode.children:
            self.node.removeChild(c)
        
        self._ensure_seps(len(new_children) - 1)
        
        for i in range(len(new_children)):
            self.outernode.appendChild(new_children[i].outernode)
            if i < len(self._seps):
                self.outernode.appendChild(self._seps[i])
    
    @event.reaction('spacing')
    def __spacing_changed(self, *events):
        pass #self.phosphor.spacing = self.spacing
    
    @event.reaction('orientation')
    def __orientation_changed(self, *events):
        if 'h' in self.orientation:
            for sep in self._seps:
                sep.classList.remove('flx-vertical')
                sep.classList.add('flx-horizontal')
        else:
            for sep in self._seps:
                sep.classList.remove('flx-horizontal')
                sep.classList.add('flx-vertical')
        self.set_divider_positions(*[sep.rel_pos for sep in self._seps])
    
    @event.reaction('children', 'children*.flex')
    def __set_flexes(self, *events):
        self.set_from_flex_values()
    
    ## Machinery
    
    def _get_available_size(self):
        bar_size = 8
        if 'h' in self.orientation:
            total_size = self.node.clientWidth
        else:
            total_size = self.node.clientHeight
        return total_size, total_size - bar_size * len(self._seps)
    
    def _ensure_seps(self, n):
        """ Ensure that we have exactly n seperators.
        """
        n = max(0, n)
        to_remove = self._seps[n:]
        self._seps = self._seps[:n]
        hv = 'flx-horizontal' if 'h' in self.orientation else 'flx-vertical'
        while len(self._seps) < n:
            sep = window.document.createElement('div')
            self._seps.append(sep)
            sep.i = len(self._seps) - 1
            sep.classList.add('flx-split-sep')
            sep.classList.add(hv)
            sep.rel_pos = 0
            sep.abs_pos = 0
    
    def _set_absolute_divider_positions(self, *positions):
        children = self.children
        bar_size = 8
        total_size, available_size = self._get_available_size()
        ori = self.orientation
        
        if len(children) != len(self._seps) + 1:
            return
        
        # Make positions equally long
        while len(positions) < len(self._seps):
            positions.append(None)
        
        # Apply positions
        for i in range(len(self._seps)):
            pos = positions[i]
            if pos is not None:
                if pos < 0:
                    pos = available_size - pos
                pos = max(0, min(available_size, pos))
                self._seps[i].abs_pos = pos
                
                # Move seps on the left, as needed
                ref_pos = pos
                for j in reversed(range(0, i)):
                    if positions[j] is None:
                        cur = self._seps[j].abs_pos
                        mi, ma = _get_min_max(ori, available_size, children[j+1].outernode)
                        self._seps[j].abs_pos = ref_pos = max(ref_pos - ma, min(ref_pos - mi, cur))
                # Move seps on the right, as needed
                ref_pos = pos
                for j in range(i+1, len(self._seps)):
                    if positions[j] is None:
                        cur = self._seps[j].abs_pos
                        mi, ma = _get_min_max(ori, available_size, children[j].outernode)
                        self._seps[j].abs_pos = ref_pos = max(ref_pos + mi, min(ref_pos + ma, cur))
        
        # Correct seps from the right edge
        ref_pos = available_size
        for j in reversed(range(0, len(self._seps))):
            cur = self._seps[j].abs_pos
            mi, ma = _get_min_max(ori, available_size, children[j+1].outernode)
            self._seps[j].abs_pos = ref_pos = max(ref_pos - ma, min(ref_pos - mi, cur))
        
        # Correct seps from the left edge
        ref_pos = 0
        for j in range(0, len(self._seps)):
            cur = self._seps[j].abs_pos
            mi, ma = _get_min_max(ori, available_size, children[j].outernode)
            self._seps[j].abs_pos = ref_pos = max(ref_pos + mi, min(ref_pos + ma, cur))
        
        # Store relative posisions
        for j in range(0, len(self._seps)):
            self._seps[j].rel_pos = self._seps[j].abs_pos / available_size
        
        # Apply
        is_horizonal = 'h' in ori
        is_reversed = 'r' in ori
        offset = 0
        last_sep_pos = 0
        for i in range(len(children)):
            widget = children[i]
            if self.outernode.children[i*2] is not widget.outernode:
                return
            ref_pos = self._seps[i].abs_pos if i < len(self._seps) else available_size
            size = ref_pos - last_sep_pos
            if True:
                # Position widget
                pos = last_sep_pos + offset
                if is_reversed is True:
                    pos = total_size - pos - size
                if is_horizonal is True:
                    widget.outernode.style.left = pos + 'px'
                    widget.outernode.style.width = size + 'px'
                    widget.outernode.style.top = '0'
                    widget.outernode.style.height = '100%'
                else:
                    widget.outernode.style.top = pos + 'px'
                    widget.outernode.style.height = size + 'px'
                    widget.outernode.style.left = '0'
                    widget.outernode.style.width = '100%'
            if i < len(self._seps):
                # Position divider
                sep = self._seps[i]
                pos = sep.abs_pos + offset
                if is_reversed is True:
                    pos = total_size - pos - bar_size
                if is_horizonal is True:
                    sep.style.left = pos + 'px'
                    sep.style.width = bar_size + 'px'
                    sep.style.top = '0'
                    sep.style.height = '100%'
                else:
                    sep.style.top = pos + 'px'
                    sep.style.height = bar_size + 'px'
                    sep.style.left = '0'
                    sep.style.width = '100%'
                offset += bar_size
                last_sep_pos = sep.abs_pos
    
    @event.emitter
    def mouse_down(self, e):
        if e.target.classList.contains("flx-split-sep"):
            e.stopPropagation()
            sep = e.target
            x_or_y1 = e.clientX if 'h' in self.orientation else e.clientY
            self._dragging = self.orientation, sep.i, sep.abs_pos, x_or_y1
        else:
            return super().mouse_down(e)
    
    @event.emitter
    def mouse_up(self, e):
        self._dragging = None
        return super().mouse_down(e)
        
    @event.emitter
    def mouse_move(self, e):
        if self._dragging is not None:
            e.stopPropagation()
            ori, i, ref_pos, x_or_y1 = self._dragging
            if ori == self.orientation:
                x_or_y2 = e.clientX if 'h' in self.orientation else e.clientY
                positions = [None for i in range(len(self._seps))]
                diff = (x_or_y1 - x_or_y2) if 'r' in ori else (x_or_y2 - x_or_y1)
                positions[i] = max(0, ref_pos + diff)
                self._set_absolute_divider_positions(*positions)
        else:
            return super().mouse_move(e)


def _get_min_max(orientation, available_size, node):
    mi = _get_min_size(available_size, node)
    ma = _get_max_size(available_size, node)
    if 'h' in orientation:
        return mi[0], ma[0]
    else:
        return mi[1], ma[1]
    # todo: can we reduce half the queries here, because half is unused?

def _get_min_size(available_size, node):
    """ Get minimum and maximum size of a node, expressed in pixels.
    """
    x = node.style.minWidth
    if x == '0' or len(x) == 0:
        x = 0
    elif x.endswith('px'):
        x = float(x[:-2])
    elif x.endswith('%'):
        x = float(x[:-1]) * available_size
    else:
        x = 0
    
    y = node.style.minHeight
    if y == '0' or len(y) == 0:
        y = 0
    elif y.endswith('px'):
        y = float(y[:-2])
    elif y.endswith('%'):
        y = float(y[:-1]) * available_size
    else:
        y = 0
    
    return x, y
    
    
def _get_max_size(available_size, node):
    
    x = node.style.maxWidth
    if x == '0':
        x = 0
    elif not x:
        x = 1e9
    elif x.endswith('px'):
        x = float(x[:-2])
    elif x.endswith('%'):
        x = float(x[:-1]) * available_size
    else:
        x = 1e9
   
    y = node.style.maxHeight
    if y == '0':
        y = 0
    elif not y:
        y = 1e9
    elif y.endswith('px'):
        y = float(y[:-2])
    elif y.endswith('%'):
        y = float(y[:-1]) * available_size
    else:
        y = 1e9
    
    return x, y
