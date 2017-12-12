"""
The HVLayout and its subclasses provide a simple mechanism to horizontally
or vertically stack child widgets.


.. UIExample:: 250
    
    from flexx import ui
    
    class Example(ui.Widget):
    
        def init(self):
            
            with ui.VBox():
                
                ui.Label(text='Flex 0 0 0')
                with ui.HBox(flex=0):
                    self.b1 = ui.Button(text='Hola', flex=0)
                    self.b2 = ui.Button(text='Hello world', flex=0)
                    self.b3 = ui.Button(text='Foo bar', flex=0)
                
                ui.Label(text='Flex 1 0 3')
                with ui.HBox(flex=0):
                    self.b1 = ui.Button(text='Hola', flex=1)
                    self.b2 = ui.Button(text='Hello world', flex=0)
                    self.b3 = ui.Button(text='Foo bar', flex=3)
                
                ui.Label(text='padding 15 (around layout)')
                with ui.HBox(flex=0, padding=15):
                    self.b1 = ui.Button(text='Hola', flex=1)
                    self.b2 = ui.Button(text='Hello world', flex=1)
                    self.b3 = ui.Button(text='Foo bar', flex=1)
                
                ui.Label(text='spacing 15 (inter-widget)')
                with ui.HBox(flex=0, spacing=15):
                    self.b1 = ui.Button(text='Hola', flex=1)
                    self.b2 = ui.Button(text='Hello world', flex=1)
                    self.b3 = ui.Button(text='Foo bar', flex=1)
                
                ui.Widget(flex=1)
                ui.Label(text='Note the spacer Widget above')


A similar example using a Split / Fix layout:

.. UIExample:: 250
    
    from flexx import ui
    
    class Example(ui.Widget):
        def init(self):
            with ui.VSplit():
                
                ui.Label(text='Flex 0 0 0', style='')
                with ui.HFix(flex=0):
                    self.b1 = ui.Button(text='Hola', flex=0)
                    self.b2 = ui.Button(text='Hello world', flex=0)
                    self.b3 = ui.Button(text='Foo bar', flex=0)
                
                ui.Label(text='Flex 1 0 3')
                with ui.HFix(flex=0):
                    self.b1 = ui.Button(text='Hola', flex=1)
                    self.b2 = ui.Button(text='Hello world', flex=0)
                    self.b3 = ui.Button(text='Foo bar', flex=3)
                
                ui.Label(text='spacing 10 (inter-widget)')
                with ui.HFix(flex=0, spacing=20):
                    self.b1 = ui.Button(text='Hola', flex=1)
                    self.b2 = ui.Button(text='Hello world', flex=1)
                    self.b3 = ui.Button(text='Foo bar', flex=1)
                
                ui.Widget(flex=1)


Interactive Box layout example:

.. UIExample:: 200
    
    from flexx import ui, event
    
    class Example(ui.HBox):
        def init(self):
            self.b1 = ui.Button(text='Horizontal', flex=0)
            self.b2 = ui.Button(text='Vertical', flex=1)
            self.b3 = ui.Button(text='Horizontal reversed', flex=2)
            self.b4 = ui.Button(text='Vertical reversed', flex=3)
        
        class JS:
            
            @event.connect('b1.mouse_down')
            def _to_horizontal(self, *events):
                self.orientation = 'h'
            
            @event.connect('b2.mouse_down')
            def _to_vertical(self, *events):
                self.orientation = 'v'
            
            @event.connect('b3.mouse_down')
            def _to_horizontal_rev(self, *events):
                self.orientation = 'hr'
            
            @event.connect('b4.mouse_down')
            def _to_vertical_r(self, *events):
                self.orientation = 'vr'


A classic high level layout:


.. UIExample:: 300

    from flexx import ui
    
    
    class Content(ui.Widget):
        def init(self):
                # Here we use Box layout, because we care about natural size
                
                with ui.HBox():
                    ui.Widget(flex=1)  # spacer
                    ui.Button(text='hello')
                    ui.Widget(flex=1)  # spacer
    
    
    class SideWidget(ui.Label):
        CSS = '.flx-SideWidget {background: #aaf; border: 2px solid black;}'
    
    
    class Example(ui.Widget):
    
        def init(self):
            # Here we use Split layout, because we define high-level layout
            
            with ui.VSplit():
                SideWidget(text='Header', flex=0, base_size=100)
                with ui.HSplit(flex=1):
                    SideWidget(text='Left', flex=0, base_size=100)
                    Content(flex=1)
                    SideWidget(text='Right', flex=0, base_size=100)
                SideWidget(text='Bottom', flex=0, base_size=100)

"""


"""
## Notes on performance and layout boundaries.

In layout one can see multiple streams of information:

- Information about available size streams downward.
- Information about minimum and maxium allowed sizes streams upward.
- Information about natural sizes streams upward.

The first two streams are not problematic, as they are very much
one-directional, and minimum/maximum sizes are often quite static.
The flow of natural size is important to obtain good looking layouts, but
adds complications because of its recursive effect; a change in size may
need several document reflows to get the layout right, which can cause
severe performance penalties if many elements are involved. Therefore it
is important to introduce "layout boundaries" in the higher levels of a UI
so that layout can be established within individual parts of the UI without
affecting the other parts.

This module implements horizontal/vertical layouts that support natural sizes
(box) and layouts that do not (fix and split). The former is implemented with
CSS flexbox (the browser does all the work, and maintains the upward stream
of natural sizes). The latter is implemented with absolute positioning (we make
JavaScript do all the work). We realize good compatibility by maintaining the
first two streams of information.

To clearify, it would be possible to implement split and fix with flexbox,
and this could result in a "nicety" that a VSplit with content can still
have a natural horizontal size (and used as such in an HBox with flex 0).
However, one can see how this will require additional document reflows
(since a change in width can change the natural height and vice versa).
Split and Fix layouts provide an intuitive way to introduce layout boundaries.

For an element to be a layout boundary it must:

- Not be display inline or inline-block
- Not have a percentage height value.
- Not have an implicit or auto height value.
- Not have an implicit or auto width value.
- Have an explicit overflow value (scroll, auto or hidden).
- Not be a descendant of a <table> element.

Most Widgets inside a HVLayout in split or fix mode conform to this:
they are typically not table elements, the layout itself uses CSS to
set display and overflow, and sets height and weight.

More reading:

- http://wilsonpage.co.uk/introducing-layout-boundaries/
- https://css-tricks.com/snippets/css/a-guide-to-flexbox/

"""

from ... import event
from ...pyscript import RawJS
from . import Layout


# _phosphor_boxpanel = RawJS("flexx.require('phosphor/lib/ui/boxpanel')")


class OrientationProp(event.Property):
    """ A property that represents a pair of float values, which can also be
    set using a scalar.
    """
    
    _default = 'h'
    
    def _validate(self, v):
        if isinstance(v, str):
            v = v.lower().replace('-', '')
        v = {'horizontal': 'h', 0: 'h', 'lefttoright': 'h',
             'vertical': 'v', 1: 'v', 'toptobottom': 'v',
             'righttoleft': 'hr', 'bottomtotop': 'vr'}.get(v, v)
        if v not in ('h', 'v', 'hr', 'vr'):
            raise ValueError('%s.orientation got unknown value %r' % (self.id, v))
        return v


class HVLayout(Layout):
    """ Layout to distribute space for widgets horizontally or vertically. 
    
    This is a versatile layout class which can operate in different
    orientations (horizontal, vertical, reversed), and in different modes:
    
    In 'fix' mode, all available space is simply distributed corresponding
    to the children's flex values. This can be convenient to e.g. split
    a layout in two halves.
    
    In 'box' mode, each widget gets at least its natural size (if available),
    and any *additional* space is distributed corresponding to the children's
    flex values. This is convenient for low-level layout of widgets, e.g. to
    align  one or more buttons. It is common to use an empty ``Widget`` with a
    flex of 1 to fill up any remaining space. This mode is based on CSS flexbox.
    
    In 'split' mode, all available space is initially distributed corresponding
    to the children's flex values. The splitters between the child widgets
    can be dragged by the user, and positioned via an action. This is useful
    to give the user more control over the (high-level) layout.
    
    In all modes, the layout is constrained by the minimum and maximum size
    of the child widgets (as set via style/CSS).
    
    Also see the convenience classes: HFix, VFix, HBox, VBox, HSplit, VSplit.
    """
    
    _DEFAULT_ORIENTATION = 'h'
    _DEFAULT_MODE = 'box'
    
    CSS = """
    
    /* === for box layout === */
    
    .flx-box {
        display: -webkit-flex;
        display: -ms-flexbox;  /* IE 10 */
        display: -ms-flex;     /* IE 11 */
        display: -moz-flex;
        display: flex;
        
        /* How space is divided when all flex-factors are 0:
           start, end, center, space-between, space-around */
        -webkit-justify-content: space-around;
        -ms-justify-content: space-around;
        -moz-justify-content: space-around;
        justify-content: space-around;
        
        /* How items are aligned in the other direction:
           center, stretch, baseline */
        -webkit-align-items: stretch;  
        -ms-align-items: stretch;
        -moz-align-items: stretch;
        align-items: stretch;
    }
    
    .flx-box.flx-horizontal {
        -webkit-flex-flow: row;
        -ms-flex-flow: row;
        -moz-flex-flow: row;
        flex-flow: row;
        width: 100%;
    }
    .flx-box.flx-vertical {
        -webkit-flex-flow: column;
        -ms-flex-flow: column;
        -moz-flex-flow: column;
        flex-flow: column;
        height: 100%; width: 100%;
    }
    .flx-box.flx-horizontal.flx-reversed {
        -webkit-flex-flow: row-reverse;
        -ms-flex-flow: row-reverse;
        -moz-flex-flow: row-reverse;
        flex-flow: row-reverse;
    }
    .flx-box.flx-vertical.flx-reversed {
        -webkit-flex-flow: column-reverse;
        -ms-flex-flow: column-reverse;
        -moz-flex-flow: column-reverse;
        flex-flow: column-reverse;
    }
    
    /* Make child widgets (and layouts) size correctly */
    .flx-box.flx-horizontal > .flx-Widget {
        height: auto;
        width: auto;
    }
    .flx-box.flx-vertical > .flx-Widget {
        width: auto;
        height: auto;
    }
    
    /* If a boxLayout is in a compound widget, we need to make that widget
       a flex container (done with JS in Widget class), and scale here */
    .flx-Widget > .flx-box {
        flex-grow: 1;
        flex-shrink: 1;
    }
    
    /* === For split and fix layout === */
    
    .flx-split > .flx-Widget {
        /* Let child widgets position well, and help them become a layout
         * boundary. We cannot do "display: block;", as that would break stuff.
         */
        position: absolute;
        overflow: hidden;
    }
    
    .flx-split.flx-horizontal > .flx-split-sep,
    .flx-split.flx-horizontal.flx-dragging {
        cursor: ew-resize;  
    }
    .flx-split.flx-vertical > .flx-split-sep,
    .flx-split.flx-vertical.flx-dragging {
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
        background: #fff;  /* hide underlying widgets */
    }
    """
    
    mode = event.StringProp('box', doc="""
        The mode in which this layout operates:
        
        * fix: all available space is distributed corresponding to the flex values.
        * box: each widget gets at least its natural size, and additional space
          is distributed corresponding to the flex values.
        * split: available space is initially distributed correspondong to the
          flex values, and can be modified by the user by dragging the splitters.
        """)
    
    orientation = OrientationProp(settable=True, doc="""
        The orientation of the child widgets. 'h' or 'v' for horizontal and
        vertical, or their reversed variants 'hr' and 'vr'. Settable with
        values: 0, 1, 'h', 'v', 'hr', 'vr', 'horizontal', 'vertical',
        'left-to-right', 'right-to-left', 'top-to-bottom', 'bottom-to-top'
        (insensitive to case and use of dashes).
        """)
    
    spacing = event.FloatProp(4, settable=True, doc="""
        The space between two child elements (in pixels).
        """)
    
    padding = event.FloatProp(1, settable=True, doc="""
        The empty space around the layout (in pixels).
        """)
    
    def __init__(self, *args, **kwargs):
        kwargs['mode'] = kwargs.get('mode', self._DEFAULT_MODE)
        kwargs['orientation'] = kwargs.get('orientation', self._DEFAULT_ORIENTATION)
        
        self._seps = []
        self._dragging = None
        
        super().__init__(*args, **kwargs)
        
        if 'Split' in self._id and 'spacing' not in kwargs:
            self.set_spacing(8)
    
    ## Actions
    
    @event.action
    def set_mode(self, mode):
        """ Set the mode (to 'box', 'split', or 'fix').
        """
        mode = str(mode)
        if mode not in ('box', 'split', 'fix'):
            raise ValueError('Invalid mode: %s.' % mode)
        self._mutate_mode(mode)
    
    @event.action
    def set_from_flex_values(self):
        """ Set the divider positions corresponding to the children's flex values.
        Only for split-mode.
        """
        # Well, we also use it to init fix-mode ...
        if self.mode == 'box': 
            return
        
        # Collect flexes
        sizes = []
        dim = 0 if 'h' in self.orientation else 1
        for widget in self.children:
            sizes.append(widget.flex[dim])
        
        # Normalize size, so that total is one
        size_sum = sum(sizes)
        if size_sum == 0:
            # Convenience: all zeros probably means to divide equally
            sizes = [1/len(sizes) for j in sizes]
        else:
            sizes = [j/size_sum for j in sizes]
        # todo: pyscript bug: if I use i here, it takes on value set above (0)
        
        # Turn sizes into positions
        total_size, available_size = self._get_available_size()
        positions = []
        pos = 0
        for i in range(len(sizes) - 1):
            pos = pos + sizes[i]
            positions.append(pos)
        
        # Apply
        self.emit('_render', dict(positions=positions))
    
    @event.action
    def set_splitter_positions(self, *positions):
        """ Set relative splitter posisions (None or values between 0 and 1).
        Only has effect in split-mode.
        """
        if self.mode != 'split':
            return
        
        positions2 = []
        for i in range(len(positions)):
            pos = positions[i]
            if pos is not None:
                pos = max(0.0, min(1.0, float(pos)))
            positions2.append(pos)
        
        self.emit('_render', dict(positions=positions2))
    
    ## General reactions and hooks
    
    @event.reaction('children*.size_min_max', 'orientation', 'spacing', 'padding')
    def __update_min_max(self, *events):
        self._check_min_max_size()
    
    def _query_min_max_size(self):
        """ Overload to also take child limits into account.
        """
        # Own limits
        mima = super()._query_min_max_size()
        
        # Add contributions of child widgets
        hori = 'h' in self.orientation
        for child in self.children:
            mima2 = child.size_min_max
            if hori is True:
                mima[0] += mima2[0]
                mima[1] += mima2[1]
                mima[2] = max(mima[2], mima2[2])
                mima[3] = min(mima[3], mima2[3])
            else:
                mima[0] = max(mima[0], mima2[0])
                mima[1] = min(mima[1], mima2[1])
                mima[2] += mima2[2]
                mima[3] += mima2[3]
        
        # Dont forget padding and spacing
        extra_padding = self.padding * 2
        extra_spacing = self.spacing * (len(self.children) - 1)
        mima[0] += extra_padding
        mima[1] += extra_padding
        mima[2] += extra_padding
        mima[3] += extra_padding
        if hori is True:
            mima[0] += extra_spacing
            mima[1] += extra_spacing
        else:
            mima[2] += extra_spacing
            mima[3] += extra_spacing
        
        return mima
    
    @event.reaction('size', 'size_min_max')
    def __size_changed(self, *events):
        self._rerender()
    
    @event.reaction('children*.size')
    def __let_children_check_suize(self, *events):
        for child in self.children:
            child.check_real_size()
    
    @event.reaction('mode')
    def __set_mode(self, *events):
        self._update_layout(self.children)  # pass children to reset their style
        
        if self.mode == 'box':
            self.outernode.classList.remove('flx-split')
            self.outernode.classList.add('flx-box')
            self._set_box_child_flexes()
            self._set_box_spacing()
        else:
            self.outernode.classList.remove('flx-box')
            self.outernode.classList.add('flx-split')
            self.set_from_flex_values()
            self._rerender()  # the above might not have triggered a rerender
    
    @event.reaction('orientation')
    def __set_orientation(self, *events):
        ori = self.orientation
        if 'h' in ori:
            self.outernode.classList.add('flx-horizontal')
            self.outernode.classList.remove('flx-vertical')
        else:
            self.outernode.classList.remove('flx-horizontal')
            self.outernode.classList.add('flx-vertical')
        if 'r' in ori:
            self.outernode.classList.add('flx-reversed')
        else:
            self.outernode.classList.remove('flx-reversed')
        
        for widget in self.children:
            widget.check_real_size()
        self._rerender()
    
    @event.reaction('padding')
    def __set_padding(self, *events):
        # todo: use main-start and cross-start instead?
        self.outernode.style['padding'] = self.padding + 'px'
        for widget in self.children:
            widget.check_real_size()
        self._rerender()
    
    def _update_layout(self, old_children, new_children=None):
        """ Can be overloaded in (Layout) subclasses.
        """
        children = self.children
        use_seps = self.mode == 'split'
        if self.mode == 'box':
            self._ensure_seps(0)
        else:
            self._ensure_seps(len(children) - 1)
        
        # Reset style of old children
        for child in old_children:
            for n in ['margin', 'left', 'width', 'top', 'height']:
                child.outernode.style[n] = ''
        
        # Remove any children
        while len(self.outernode.children) > 0:
            c =self.outernode.children[0]
            self.outernode.removeChild(c)
        
        # Add new children and maybe interleave with separater widgets
        for i in range(len(children)):
            self.outernode.appendChild(children[i].outernode)
            if use_seps and i < len(self._seps):
                self.outernode.appendChild(self._seps[i])
    
    def _ensure_seps(self, n):
        """ Ensure that we have exactly n seperators.
        """
        n = max(0, n)
        to_remove = self._seps[n:]
        self._seps = self._seps[:n]
        # hv = 'flx-horizontal' if 'h' in self.orientation else 'flx-vertical'
        while len(self._seps) < n:
            sep = window.document.createElement('div')
            self._seps.append(sep)
            sep.i = len(self._seps) - 1
            sep.classList.add('flx-split-sep')
            # sep.classList.add(hv)
            sep.rel_pos = 0
            sep.abs_pos = 0
    
    def _rerender(self):
        """ Invoke a re-render. Only necessary for fix/split mode.
        """
        self.emit('_render')
    
    ## Reactions for box mode
    
    @event.reaction('orientation', 'children', 'children*.flex')
    def _set_box_child_flexes(self, *events):
        if self.mode != 'box':
            return
        ori = self.orientation
        i = 0 if ori in (0, 'h', 'hr') else 1
        for widget in self.children:
            _applyBoxStyle(widget.outernode, 'flex-grow', widget.flex[i])
            _applyBoxStyle(widget.outernode, 'flex-shrink', widget.flex[i] or 1)  # default value is 1
        for widget in self.children:
            widget.check_real_size()
    
    @event.reaction('spacing', 'orientation', 'children')
    def _set_box_spacing(self, *events):
        if self.mode != 'box':
            return 
        ori = self.orientation
        children_events = [ev for ev in events if ev.type == 'children']
        old_children = children_events[0].old_value if children_events else []
        children = self.children
        # Reset
        for child in children:
            child.outernode.style['margin-top'] = ''
            child.outernode.style['margin-left'] = ''
        for child in old_children:
            child.outernode.style['margin-top'] = ''
            child.outernode.style['margin-left'] = ''
        # Set
        margin = 'margin-top' if ori in (1, 'v', 'vr') else 'margin-left'
        if children.length:
            if ori in ('vr', 'hr'):
                children[-1].outernode.style[margin] = '0px'
                for child in children[:-1]:
                    child.outernode.style[margin] = self.spacing + 'px'
            else:
                children[0].outernode.style[margin] = '0px'
                for child in children[1:]:
                    child.outernode.style[margin] = self.spacing + 'px'
        for widget in children:
            widget.check_real_size()
    
    ## Reactions and machinerey for fix/split mode
    
    def _get_available_size(self):
        bar_size = self.spacing
        pad_size = self.padding
        if 'h' in self.orientation:
            total_size = self.outernode.clientWidth
        else:
            total_size = self.outernode.clientHeight
        return total_size, total_size - bar_size * len(self._seps) - 2 * pad_size
    
    @event.reaction('spacing')
    def __spacing_changed(self, *events):
        self._rerender()
    
    @event.reaction('children', 'children*.flex')
    def _set_split_from_flexes(self, *events):
        if self.mode != 'box':
            self.set_from_flex_values()
    
    @event.reaction('!_render')
    def __render(self, *events):
        """ Set the slider positions, subject to constraints.
        """
        # todo: this is a use-case where it would be nice to be able to notify
        # the loop that this reacion does not care about order in relation to
        # other events as much; we'd much rather process the events at once.
        
        if self.mode != 'box':
            
            # Apply specific positional changes
            re_apply = False
            for ev in events:
                if ev.positions:
                    self.__apply_positions(ev.positions)
                else:
                    re_apply = True
            # Maybe apply current relative positions
            if re_apply:
                self.__apply_positions([sep.rel_pos for sep in self._seps])
            # Apply positions to child widgets
            self.__render_positions()
       
        # Size may have changed - also for box
        for child in self.children:
            child.check_real_size()
    
    def __apply_positions(self, input_positions):
        """ Apply a position-tuple. Can have Nones to only modify one
        splitter position. Sets sep.abs_pos and sep.rel_pos on each separator.
        """
        
        children = self.children
        bar_size = self.spacing
        pad_size = self.padding
        total_size, available_size = self._get_available_size()
        ori = self.orientation
        
        if len(children) != len(self._seps) + 1:
            return
        
        # Make positions list long enough, and set elements absolute
        positions = []
        for i in range(len(input_positions)): 
            pos = input_positions[i]
            if pos is not None:
                pos = pos * available_size
            positions.append(pos)
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
                        mi, ma = _get_min_max(children[j+1], ori)
                        self._seps[j].abs_pos = ref_pos = max(ref_pos - ma, min(ref_pos - mi, cur))
                # Move seps on the right, as needed
                ref_pos = pos
                for j in range(i+1, len(self._seps)):
                    if positions[j] is None:
                        cur = self._seps[j].abs_pos
                        mi, ma = _get_min_max(children[j], ori)
                        self._seps[j].abs_pos = ref_pos = max(ref_pos + mi, min(ref_pos + ma, cur))
        
        # Correct seps from the right edge
        ref_pos = available_size
        for j in reversed(range(0, len(self._seps))):
            cur = self._seps[j].abs_pos
            mi, ma = _get_min_max(children[j+1], ori)
            self._seps[j].abs_pos = ref_pos = max(ref_pos - ma, min(ref_pos - mi, cur))
        
        # Correct seps from the left edge
        ref_pos = 0
        for j in range(0, len(self._seps)):
            cur = self._seps[j].abs_pos
            mi, ma = _get_min_max(children[j], ori)
            self._seps[j].abs_pos = ref_pos = max(ref_pos + mi, min(ref_pos + ma, cur))
        
        # Store relative posisions
        for j in range(0, len(self._seps)):
            self._seps[j].rel_pos = self._seps[j].abs_pos / available_size
    
    def __render_positions(self):
        """ Use the absolute positions on the seps to apply positions to
        the child elements and separators.
        """
        
        children = self.children
        bar_size = self.spacing
        pad_size = self.padding
        total_size, available_size = self._get_available_size()
        ori = self.orientation
        
        if len(children) != len(self._seps) + 1:
            return
        
        # Apply
        is_horizonal = 'h' in ori
        is_reversed = 'r' in ori
        offset = pad_size
        last_sep_pos = 0
        for i in range(len(children)):
            widget = children[i]
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
                    widget.outernode.style.top = pad_size + 'px'
                    widget.outernode.style.height = 'calc(100% - ' + 2*pad_size + 'px)'
                else:
                    widget.outernode.style.left = pad_size + 'px'
                    widget.outernode.style.width = 'calc(100% - ' + 2*pad_size + 'px)'
                    widget.outernode.style.top = pos + 'px'
                    widget.outernode.style.height = size + 'px'
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
        if self.mode == 'split' and e.target.classList.contains("flx-split-sep"):
            e.stopPropagation()
            sep = e.target
            x_or_y1 = e.clientX if 'h' in self.orientation else e.clientY
            self._dragging = self.orientation, sep.i, sep.rel_pos, x_or_y1
            self.outernode.classList.add('flx-dragging')
        else:
            return super().mouse_down(e)
    
    @event.emitter
    def mouse_up(self, e):
        self._dragging = None
        self.outernode.classList.remove('flx-dragging')
        return super().mouse_down(e)
    
    @event.emitter
    def mouse_move(self, e):
        if self._dragging is not None:
            e.stopPropagation()
            ori, i, ref_pos, x_or_y1 = self._dragging
            if ori == self.orientation:
                x_or_y2 = e.clientX if 'h' in self.orientation else e.clientY
                total_size, available_size = self._get_available_size()
                positions = [None for j in range(len(self._seps))]
                diff = (x_or_y1 - x_or_y2) if 'r' in ori else (x_or_y2 - x_or_y1)
                positions[i] = max(0, ref_pos + diff / available_size)
                self.emit('_render', dict(positions=positions))
        else:
            return super().mouse_move(e)


## Util funcs

def _applyBoxStyle(e, sty, value):
    for prefix in ['-webkit-', '-ms-', '-moz-', '']:
        e.style[prefix + sty] = value


def _get_min_max(widget, ori):
    mima = widget.size_min_max
    if 'h' in ori:
        return mima[0], mima[1]
    else:
        return mima[2], mima[3]


## Convenience subclasses

class HBox(HVLayout):
    """ Horizontal layout that tries to give each widget its natural size and
    distributes any remaining space corresponding to the widget's flex values.
    (I.e. an HVLayout with orientation 'h' and mode 'box'.)
    """
    _DEFAULT_ORIENTATION = 'h'
    _DEFAULT_MODE = 'box'


class VBox(HVLayout):
    """ Vertical layout that tries to give each widget its natural size and
    distributes any remaining space corresponding to the widget's flex values.
    (I.e. an HVLayout with orientation 'v' and mode 'box'.)
    """
    _DEFAULT_ORIENTATION = 'v'
    _DEFAULT_MODE = 'box'


class HFix(HVLayout):
    """ Horizontal layout that distributes the available space corresponding
    to the widget's flex values.
    (I.e. an HVLayout with orientation 'h' and mode 'fix'.)
    """
    _DEFAULT_ORIENTATION = 'h'
    _DEFAULT_MODE = 'fix'


class VFix(HVLayout):
    """ Vertical layout that distributes the available space corresponding
    to the widget's flex values.
    (I.e. an HVLayout with orientation 'v' and mode 'fix'.)
    """
    _DEFAULT_ORIENTATION = 'v'
    _DEFAULT_MODE = 'fix'


class HSplit(HVLayout):
    """ Horizontal layout that initially distributes the available space
    corresponding to the widget's flex values, and has draggable splitters.
    By default, this layout has a slightly larger spacing between the widgets.
    (I.e. an HVLayout with orientation 'h' and mode 'split'.)
    """
    _DEFAULT_ORIENTATION = 'h'
    _DEFAULT_MODE = 'split'


class VSplit(HVLayout):
    """ Vertical layout that initially distributes the available space
    corresponding to the widget's flex values, and has draggable splitters.
    By default, this layout has a slightly larger spacing between the widgets.
    (I.e. an HVLayout with orientation 'v' and mode 'split'.)
    """
    _DEFAULT_ORIENTATION = 'v'
    _DEFAULT_MODE = 'split'
