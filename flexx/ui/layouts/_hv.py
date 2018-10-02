""" HVLayout

The HVLayout and its subclasses provide a simple mechanism to horizontally
or vertically stack child widgets. This can be done in different *modes*:
box mode is suited for aligning content where natural size matters. The
fix mode and split mode are more suited for high-level layout. See
the HVLayout class for details.


Interactive Box layout example:

.. UIExample:: 200

    from flexx import app, event, ui

    class Example(ui.HBox):
        def init(self):
            self.b1 = ui.Button(text='Horizontal', flex=0)
            self.b2 = ui.Button(text='Vertical', flex=1)
            self.b3 = ui.Button(text='Horizontal reversed', flex=2)
            self.b4 = ui.Button(text='Vertical reversed', flex=3)

        @event.reaction('b1.pointer_down')
        def _to_horizontal(self, *events):
            self.set_orientation('h')

        @event.reaction('b2.pointer_down')
        def _to_vertical(self, *events):
            self.set_orientation('v')

        @event.reaction('b3.pointer_down')
        def _to_horizontal_rev(self, *events):
            self.set_orientation('hr')

        @event.reaction('b4.pointer_down')
        def _to_vertical_r(self, *events):
            self.set_orientation('vr')

Also see examples: :ref:`app_layout.py`, :ref:`splitters.py`,
:ref:`box_vs_fix_layout.py`, :ref:`mondriaan.py`.

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
they are typically not table elements, the Widget sets overflow, the layout
itself uses CSS to set display, and sets height and weight.

More reading:

- http://wilsonpage.co.uk/introducing-layout-boundaries/
- https://css-tricks.com/snippets/css/a-guide-to-flexbox/

"""

from ... import event, app
from ...event import Property
from . import Layout


class OrientationProp(Property):
    """ A property that represents a pair of float values, which can also be
    set using a scalar.
    """

    _default = 'h'

    def _validate(self, v, name, data):
        if isinstance(v, str):
            v = v.lower().replace('-', '')
        v = {'horizontal': 'h', 0: 'h', 'lefttoright': 'h',
             'vertical': 'v', 1: 'v', 'toptobottom': 'v',
             'righttoleft': 'hr', 'bottomtotop': 'vr'}.get(v, v)
        if v not in ('h', 'v', 'hr', 'vr'):
            raise ValueError('%s.orientation got unknown value %r' % (self.id, v))
        return v


class HVLayout(Layout):
    """ A layout widget to distribute child widgets horizontally or vertically.

    This is a versatile layout class which can operate in different
    orientations (horizontal, vertical, reversed), and in different modes:

    In 'fix' mode, all available space is simply distributed corresponding
    to the children's flex values. This can be convenient to e.g. split
    a layout in two halves.

    In 'box' mode, each widget gets at least its natural size (if available),
    and any *additional* space is distributed corresponding to the children's
    flex values. This is convenient for low-level layout of widgets, e.g. to
    align  one or more buttons. It is common to use flex values of zero to
    give widgets just the size that they needs and use an empty widget with a
    flex of 1 to fill up any remaining space. This mode is based on CSS flexbox.

    In 'split' mode, all available space is initially distributed corresponding
    to the children's flex values. The splitters between the child widgets
    can be dragged by the user and positioned via an action. This is useful
    to give the user more control over the (high-level) layout.

    In all modes, the layout is constrained by the minimum and maximum size
    of the child widgets (as set via style/CSS). Note that flexbox (and thus
    box mode) may not honour min/max sizes of widgets in child layouts.

    Note that widgets with a flex value of zero may collapse if used inside
    a fix/split layout, or in a box layout but lacking a natural size. This
    can be resolved by assigning a minimum width/height to the widget. The
    exception is if all child widgets have a flex value of zero, in which
    case the available space is divided equally.

    The ``node`` of this widget is a
    `<div> <https://developer.mozilla.org/docs/Web/HTML/Element/div>`_. The
    outer nodes of the child widgets are layed-out using JavaScript of CSS,
    depending on the mode.
    
    Also see the convenience classes: HFix, VFix, HBox, VBox, HSplit, VSplit.
    """

    _DEFAULT_ORIENTATION = 'h'
    _DEFAULT_MODE = 'box'

    CSS = """

    /* === for box layout === */

    .flx-HVLayout > .flx-Widget {
        margin: 0; /* the layout handles the margin */
     }

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
        /* overflow is set in Widget.CSS, setting here breaks scrollable widgets
         */
        position: absolute;
    }

    .flx-split.flx-dragging { /* Fix for odd drag behavior on Chrome */
        -webkit-user-select: none;
        -moz-user-select: none;
        -ms-user-select: none;
        user-select: none;
    }
    .flx-split.flx-dragging iframe {  /* disable iframe during drag */
        pointer-events: none;
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
        background: rgba(0, 0, 0, 0); /* transparent */
        /* background: #fff;  /* hide underlying widgets */
    }
    """

    mode = event.EnumProp(('box', 'fix', 'split'), settable=True, doc="""
        The mode in which this layout operates:

        * 'BOX': (default) each widget gets at least its natural size, and
          additional space is distributed corresponding to the flex values.
        * 'FIX': all available space is distributed corresponding to the flex values.
        * 'SPLIT': available space is initially distributed correspondong to the
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

    # splitter_positions = event.TupleProp(doc="""  xx local property!
    splitter_positions = app.LocalProperty(doc="""
        The preferred relative positions of the splitters. The actual
        positions are subject to minsize and maxsize constraints
        (and natural sizes for box-mode).
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
    def set_from_flex_values(self):
        """ Set the divider positions corresponding to the children's flex values.
        Only has a visual effect in split-mode.
        """
        # Note that we still use it for fix mode to initialize it, and in box
        # mode to set splitter_positions prop, for consistency.

        # Collect flexes
        sizes = []
        dim = 0 if 'h' in self.orientation else 1
        for widget in self.children:
            sizes.append(widget.flex[dim])

        # Normalize size, so that total is one
        size_sum = 0 if len(sizes) == 0 else sum(sizes)
        if size_sum == 0:
            # Convenience: all zeros probably means to divide equally
            sizes = [1/len(sizes) for i in sizes]
        else:
            sizes = [i/size_sum for i in sizes]

        # Turn sizes into positions
        positions = []
        pos = 0
        for i in range(len(sizes) - 1):
            pos = pos + sizes[i]
            positions.append(pos)

        # Apply
        self._mutate_splitter_positions(positions)

    @event.action
    def set_splitter_positions(self, *positions):
        """ Set relative splitter posisions (None or values between 0 and 1).
        Only usable in split-mode.
        """
        # todo: technically, we could allow this in fix-mode too, but *should* we?
        if self.mode != 'SPLIT':
            return

        positions2 = []
        for i in range(len(positions)):
            pos = positions[i]
            if pos is not None:
                pos = max(0.0, min(1.0, float(pos)))
            positions2.append(pos)

        self._mutate_splitter_positions(positions2)

    @event.emitter
    def user_splitter_positions(self, *positions):
        """ Event emitted when the splitter is positioned by the user.
        The event has a ``positions`` attribute.
        """
        if self.mode != 'SPLIT':
            return None  # do not emit

        positions2 = []
        for i in range(len(positions)):
            pos = positions[i]
            if pos is not None:
                pos = max(0.0, min(1.0, float(pos)))
            positions2.append(pos)

        self.set_splitter_positions(*positions)
        return {'positions': positions}

    ## General reactions and hooks

    def _query_min_max_size(self):
        """ Overload to also take child limits into account.
        """

        # This streams information about min and max sizes upward, for
        # split and fix mode. Most flexbox implementations don't seem to
        # look for min/max sizes of their children. We could set min-width and
        # friends at the layout to help flexbox a bit, but that would possibly
        # overwrite a user-set value. Hopefully flexbox will get fixed soon.
        
        hori = 'h' in self.orientation
        
        # Own limits
        mima0 = super()._query_min_max_size()
        
        # Init limits for children
        if hori is True:
            mima1 = [0, 0, 0, 1e9]
        else:
            mima1 = [0, 1e9, 0, 0]
        
        # Collect contributions of child widgets?
        if self.minsize_from_children:
            for child in self.children:
                mima2 = child._size_limits
                if hori is True:
                    mima1[0] += mima2[0]
                    mima1[1] += mima2[1]
                    mima1[2] = max(mima1[2], mima2[2])
                    mima1[3] = min(mima1[3], mima2[3])
                else:
                    mima1[0] = max(mima1[0], mima2[0])
                    mima1[1] = min(mima1[1], mima2[1])
                    mima1[2] += mima2[2]
                    mima1[3] += mima2[3]
        
        # Set unset max sizes
        if mima1[1] == 0:
            mima1[1] = 1e9
        if mima1[3] == 0:
            mima1[3] = 1e9
        
        # Add padding and spacing
        if self.minsize_from_children:
            extra_padding = self.padding * 2
            extra_spacing = self.spacing * (len(self.children) - 1)
            for i in range(4):
                mima1[i] += extra_padding
            if hori is True:
                mima1[0] += extra_spacing
                mima1[1] += extra_spacing
            else:
                mima1[2] += extra_spacing
                mima1[3] += extra_spacing
        
        # Combine own limits with limits of children
        return [max(mima1[0], mima0[0]),
                min(mima1[1], mima0[1]),
                max(mima1[2], mima0[2]),
                min(mima1[3], mima0[3])]

    @event.reaction('size', '_size_limits', mode='greedy')
    def __size_changed(self, *events):
        self._rerender()

    @event.reaction('children*.size', mode='greedy')
    def __let_children_check_size(self, *events):
        for child in self.children:
            child.check_real_size()

    @event.reaction('mode')
    def __set_mode(self, *events):
        # reset children style
        for child in self.children:
            self._release_child(child)

        if self.mode == 'BOX':
            self.outernode.classList.remove('flx-split')
            self.outernode.classList.add('flx-box')
            self._set_box_child_flexes()
            self._set_box_spacing()
        else:
            self.outernode.classList.remove('flx-box')
            self.outernode.classList.add('flx-split')
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
        self.outernode.style['padding'] = self.padding + 'px'
        for widget in self.children:
            widget.check_real_size()
        self._rerender()

    def _release_child(self, widget):
        for n in ['margin', 'left', 'width', 'top', 'height']:
            widget.outernode.style[n] = ''

    def _render_dom(self):
        children = self.children
        mode = self.mode
        use_seps = mode == 'SPLIT'
        if mode == 'BOX':
            self._ensure_seps(0)
        else:
            self._ensure_seps(len(children) - 1)

        # Add new children and maybe interleave with separater widgets
        nodes = []
        for i in range(len(children)):
            nodes.append(children[i].outernode)
            if use_seps and i < len(self._seps):
                nodes.append(self._seps[i])
        return nodes

    def _ensure_seps(self, n):
        """ Ensure that we have exactly n seperators.
        """
        global window
        n = max(0, n)
        to_remove = self._seps[n:]  # noqa
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

    @event.action
    def _rerender(self):
        """ Invoke a re-render. Only necessary for fix/split mode.
        """
        if self.mode == 'BOX':
            # Sizes may have changed
            for child in self.children:
                child.check_real_size()
        else:
            # Enfore a rerender by mutating splitter_positions
            sp1 = ()
            sp2 = self.splitter_positions
            sp2 = () if sp2 is None else sp2
            if len(sp2) == 0:
                sp1 = (1, )
            self._mutate_splitter_positions(sp1)
            self._mutate_splitter_positions(sp2)

    ## Reactions for box mode

    @event.reaction('orientation', 'children', 'children*.flex', mode='greedy')
    def _set_box_child_flexes(self, *events):
        if self.mode != 'BOX':
            return
        ori = self.orientation
        i = 0 if ori in (0, 'h', 'hr') else 1
        for widget in self.children:
            _applyBoxStyle(widget.outernode, 'flex-grow', widget.flex[i])
            _applyBoxStyle(widget.outernode, 'flex-shrink', widget.flex[i] or 1)
        for widget in self.children:
            widget.check_real_size()

    @event.reaction('spacing', 'orientation', 'children', mode='greedy')
    def _set_box_spacing(self, *events):
        if self.mode != 'BOX':
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

    @event.reaction('children', 'children*.flex', mode='greedy')
    def _set_split_from_flexes(self, *events):
        self.set_from_flex_values()

    @event.reaction
    def __watch_splitter_positions(self):
        """ Set the slider positions, subject to constraints.
        """
        # This is an implicit reaction, triggered by splitter_positions.
        # Implicit reactions collect events in a way that is less sensitive
        # to ordering with other reactions. We emit the rerender event instead
        # of calling the render method, otherwise that would trigger a lot
        # of unintended propery usage!
        if self.mode != 'BOX':
            self.splitter_positions
            self.emit('_render')

        # todo: we could do more thottling here, or use a scheme to tell the loop
        # that this reaction does not care about event ordering. (issue #426)

    def __apply_one_splitter_pos(self, index, pos):
        """ Set the absolute position of one splitter. Called from move event.
        """

        # Note that the min/max constraints are applied in a rather different
        # way as they are in the render method, because here the goal is to
        # shift neighboring widgets around, while in rendering the purpose is
        # to distribute superfluous/missing space equally.

        children = self.children
        total_size, available_size = self._get_available_size()
        ori = self.orientation

        if index >= len(self._seps):
            return

        # Apply the position
        if pos < 0:
            pos = available_size - pos
        pos = max(0, min(available_size, pos))
        abs_positions = [sep.abs_pos for sep in self._seps]
        abs_positions[index] = pos

        # Move seps on the left, as needed
        ref_pos = pos
        for i in reversed(range(0, index)):
            cur = abs_positions[i]
            mi, ma = _get_min_max(children[i+1], ori)
            abs_positions[i] = ref_pos = max(ref_pos - ma, min(ref_pos - mi, cur))

        # Move seps on the right, as needed
        ref_pos = pos
        for i in range(index+1, len(abs_positions)):
            cur = abs_positions[i]
            mi, ma = _get_min_max(children[i], ori)
            abs_positions[i] = ref_pos = max(ref_pos + mi, min(ref_pos + ma, cur))

        # Correct seps from the right edge
        ref_pos = available_size
        for i in reversed(range(0, len(abs_positions))):
            cur = abs_positions[i]
            mi, ma = _get_min_max(children[i+1], ori)
            abs_positions[i] = ref_pos = max(ref_pos - ma, min(ref_pos - mi, cur))

        # Correct seps from the left edge
        ref_pos = 0
        for i in range(0, len(abs_positions)):
            cur = abs_positions[i]
            mi, ma = _get_min_max(children[i], ori)
            abs_positions[i] = ref_pos = max(ref_pos + mi, min(ref_pos + ma, cur))

        # Set (relative) splitter positions. This may seem like a detour, but
        # this way the splits will scale nicely e.g. during resizing.
        self.user_splitter_positions(*[pos/available_size for pos in abs_positions])

    def __apply_positions(self):
        """ Set sep.abs_pos and sep.rel_pos on each separator.
        Called by __render_positions.
        """

        children = self.children
        total_size, available_size = self._get_available_size()
        ori = self.orientation
        positions = self.splitter_positions

        if len(positions) != len(self._seps):
            return
        if len(children) != len(self._seps) + 1:
            return

        # Apply absolute positions
        for i in range(len(positions)):
            self._seps[i].abs_pos = positions[i] * available_size

        # Collect info for each widget ...
        # given: the width/height that the widget seems to get at this point
        # mi/ma: min/max size
        # can_give: how much it has more than it needs; negative means it needs more
        # can_receive: how much it has less than the max; negative means it needs less
        ww = []
        ref_pos = 0
        for i in range(len(children)):
            w = {}
            ww.append(w)
            if i < len(self._seps):
                w.given = self._seps[i].abs_pos - ref_pos
                ref_pos = self._seps[i].abs_pos
            else:
                w.given = available_size - ref_pos
            w.mi, w.ma = _get_min_max(children[i], ori)
            w.can_give = w.given - w.mi
            w.can_receive = w.ma - w.given
            w.has = w.given  # may be reset

        # Give each widget what it needs
        net_size = 0
        for w in ww:
            if w.can_give < 0:  # i.e. must take
                net_size += w.can_give
                w.has = w.mi
                w.can_give = 0
                w.can_receive = w.ma - w.has
            elif w.can_receive < 0:  # i.e. must give
                net_size -= w.can_receive
                w.has = w.ma
                w.can_receive = 0
                w.can_give = w.has - w.mi

        # Now divide remaining space (or lack thereof) equally
        ww2 = ww.copy()
        for iter in range(4):  # safe for-loop
            if abs(net_size) < 0.5 or len(ww2) == 0:
                break
            size_for_each = net_size / len(ww2)
            for i in reversed(range(len(ww2))):
                w = ww2[i]
                if net_size > 0:  # size to divide where we can
                    if w.can_receive > 0:
                        gets = min(w.can_receive, size_for_each)
                        net_size -= gets
                        w.can_receive -= gets
                        w.has += gets
                    if w.can_receive <= 0:
                        ww2.pop(i)
                else:  # size to take where we can
                    if w.can_give > 0:
                        take = min(w.can_give, -size_for_each)
                        net_size += take
                        w.can_give -= take
                        w.has -= take
                    if w.can_give <= 0:
                        ww2.pop(i)

        # Apply new sep positions
        ref_pos = 0
        for i in range(len(self._seps)):
            ref_pos += ww[i].has
            self._seps[i].abs_pos = ref_pos

        # The assertion below might not hold if the layout is too
        # small/large to fulfil constraints:
        # assert abs(ref_pos + ww[-1].has - available_size)

        # Store relative posisions, for good measure
        for i in range(0, len(self._seps)):
            self._seps[i].rel_pos = self._seps[i].abs_pos / available_size

    @event.reaction('!_render', mode='greedy')
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

        # First apply absolute positions based on splitter_positions attribute.
        self.__apply_positions()

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

        # Child sizes have likely changed
        for child in children:
            child.check_real_size()

    @event.emitter
    def pointer_down(self, e):
        if self.mode == 'SPLIT' and e.target.classList.contains("flx-split-sep"):
            e.stopPropagation()
            sep = e.target
            t = e.changedTouches[0] if e.changedTouches else e
            x_or_y1 = t.clientX if 'h' in self.orientation else t.clientY
            self._dragging = self.orientation, sep.i, sep.abs_pos, x_or_y1
            self.outernode.classList.add('flx-dragging')
        else:
            return super().pointer_down(e)

    @event.emitter
    def pointer_up(self, e):
        self._dragging = None
        self.outernode.classList.remove('flx-dragging')
        return super().pointer_down(e)

    @event.emitter
    def pointer_move(self, e):
        if self._dragging is not None:
            e.stopPropagation()
            e.preventDefault()  # prevent drag-down-refresh on mobile devices
            ori, i, ref_pos, x_or_y1 = self._dragging
            if ori == self.orientation:
                t = e.changedTouches[0] if e.changedTouches else e
                x_or_y2 = t.clientX if 'h' in self.orientation else t.clientY
                diff = (x_or_y1 - x_or_y2) if 'r' in ori else (x_or_y2 - x_or_y1)
                self.__apply_one_splitter_pos(i, max(0, ref_pos + diff))
        else:
            return super().pointer_move(e)


## Util funcs

def _applyBoxStyle(e, sty, value):
    for prefix in ['-webkit-', '-ms-', '-moz-', '']:
        e.style[prefix + sty] = value


def _get_min_max(widget, ori):
    mima = widget._size_limits
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
