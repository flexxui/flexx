""" Layout widgets
"""

from ..pyscript import js
from ..properties import Prop, Instance, Str, Tuple, Float, Int

from .widget import Widget


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
        width: 100%;
        height: 100%;
        margin: 0px;
        padding: 0px;
        border-spacing: 0px;
        border: 0px;
    }
    
    """
    
    @js
    def _js_applyBoxStyle(self, e, sty, value):
        for prefix in ['-webkit-', '-ms-', '-moz-', '']:
            e.style[prefix + sty] = value



class Box(Layout):
    """ Abstract class for HBox and VBox
    """
    
    CSS = """
    .flx-hbox, .flx-vbox {
        display: -webkit-flex;
        display: -ms-flexbox;  /* IE 10 */
        display: -ms-flex;     /* IE 11 */
        display: -moz-flex;
        display: flex;
        
        justify-content: stretch;  /* start, end, center, space-between, space-around */
        align-items: stretch;
        align-content: stretch;
    }
    
    */
    .box-align-center { -webkit-align-items: center; -ms-align-items: center; -moz-align-items: center; align-items: center; }
    .box-align-center { -webkit-align-items: center; -ms-align-items: center; -moz-align-items: center; align-items: center; }
    */
    
    .flx-hbox > .flx-hbox, .flx-hbox > .flx-vbox {
        width: auto;
    }
    .flx-vbox > .flx-hbox, .flx-vbox > .flx-vbox {
        height: auto;
    }
    """
    
    margin = Float()
    spacing = Float()
    
    @js
    def _js_create_node(self):
        this.node = document.createElement('div')
    
    @js
    def _js_add_child(self, widget):
        self._applyBoxStyle(widget.node, 'flex-grow', widget.flex)
        #if widget.flex > 0:  widget.applyBoxStyle(el, 'flex-basis', 0)
        self._spacing_changed('spacing', self.spacing, self.spacing)
        super()._add_child(widget)
    
    @js
    def _js_remove_child(self, widget):
        self._spacing_changed('spacing', self.spacing, self.spacing)
        super()._remove_child(widget)
    
    @js
    def _js_spacing_changed(self, name, old, spacing):
        if self.children.length:
            self.children[0].node.style['margin-left'] = '0px'
            for child in self.children[1:]:
                child.node.style['margin-left'] = spacing + 'px'
    
    @js
    def _js_margin_changed(self, name, old, margin):
        self.node.style['padding'] = margin + 'px'


class HBox(Box):
    """ Layout widget to align elements horizontally.
    """
    
    CSS = """
    .flx-hbox {
        -webkit-flex-flow: row;
        -ms-flex-flow: row;
        -moz-flex-flow: row;
        flex-flow: row;
        width: 100%;
        /*border: 1px dashed #44e;*/
    }
    """
    
    @js
    def _js_init(self):
        super()._init()
        # align-items: flex-start, flex-end, center, baseline, stretch
        self._applyBoxStyle(self.node, 'align-items', 'center')
        #justify-content: flex-start, flex-end, center, space-between, space-around
        self._applyBoxStyle(self.node, 'justify-content', 'space-around')


class VBox(Box):
    """ Layout widget to align elements vertically.
    """
    
    CSS = """
    .flx-vbox {
        -webkit-flex-flow: column;
        -ms-flex-flow: column;
        -moz-flex-flow: column;
        flex-flow: column;
        height: 100%;
        width: 100%;
        /*border: 1px dashed #e44;*/
    }
    """
    
    @js
    def _js_init(self):
        super()._init()
        self._applyBoxStyle(self.node, 'align-items', 'stretch')
        self._applyBoxStyle(self.node, 'justify-content', 'space-around')


class BaseTableLayout(Layout):
    """ Abstract base class for layouts that use an HTML table.
    """
    
    CSS = """
    
    /* Behave well inside hbox/vbox, 
       we assume no layouts to be nested inside a table layout */
    .flx-hbox > .flx-basetablelayout {
        width: auto;
    }
    .flx-vbox > .flx-basetablelayout {
        height: auto;
    }

    /* In flexed cells, occupy the full space */
    td.vflex > .flx-widget {
        height: 100%;
    }
    td.hflex > .flx-widget {
        width: 100%;
    }
    """
    
    @js
    def _js_init(self):
        super()._init()
        self.connect_event('resize', (self, '_adapt_to_size_change'))
    
    @js
    def _js_apply_table_layout(self):
        table = self.node
        AUTOFLEX = 729  # magic number unlikely to occur in practice
        
        # Get table dimensions
        nrows = len(table.children)
        ncols = 0
        for i in range(len(table.children)):
            row = table.children[i]
            ncols = max(ncols, len(row.children))
        if ncols == 0 and nrows == 0:
            return
        
        # Collect flexes
        vflexes = []
        hflexes = []
        for i in range(nrows):
            row = table.children[i]
            for j in range(ncols):
                col = row.children[j]
                if (col is undefined) or (len(col.children) == 0):
                    continue
                vflexes[i] = max(vflexes[i] or 0, col.children[0].vflex or 0)
                hflexes[j] = max(hflexes[j] or 0, col.children[0].hflex or 0)
        
        # What is the cumulative "flex-value"?
        cum_vflex = vflexes.reduce(lambda pv, cv: pv + cv, 0)
        cum_hflex = hflexes.reduce(lambda pv, cv: pv + cv, 0)
        
        # If no flexes are given; assign each equal
        if (cum_vflex == 0):
            for i in range(len(vflexes)):
                vflexes[i] = AUTOFLEX
            cum_vflex = len(vflexes) * AUTOFLEX
        if (cum_hflex == 0):
            for i in range(len(hflexes)):
                hflexes[i] = AUTOFLEX
            cum_hflex = len(hflexes) * AUTOFLEX
        
        # Assign css class and height/weight to cells
        for i in range(nrows):
            row = table.children[i]
            row.vflex = vflexes[i] or 0  # Store for use during resizing
            for j in range(ncols):
                col = row.children[j];
                if (col is undefined) or (col.children.length is 0):
                    continue
                self._apply_cell_layout(row, col, vflexes[i], hflexes[j], cum_vflex, cum_hflex)
    
    @js
    def _js_adapt_to_size_change(self, event):
        """ This function adapts the height (in percent) of the flexible rows
        of a layout. This is needed because the percent-height applies to the
        total height of the table. This function is called whenever the
        table resizes, and adjusts the percent-height, taking the available 
        remaining table height into account. This is not necesary for the
        width, since percent-width in colums *does* apply to available width.
        """
        table = self.node  # or event.target
        #print('heigh changed', event.heightChanged, event.owner.__id)
        
        if event.heightChanged:
            
            # Set one flex row to max, so that non-flex rows have their
            # minimum size. The table can already have been stretched
            # a bit, causing the total row-height in % to not be
            # sufficient from keeping the non-flex rows from growing.
            for i in range(len(table.children)):
                row = table.children[i]
                if (row.vflex > 0):
                    row.style.height = '100%'
                    break
            
            # Get remaining height: subtract height of each non-flex row
            remainingHeight = table.clientHeight
            cum_vflex = 0
            for i in range(len(table.children)):
                row = table.children[i]
                cum_vflex += row.vflex
                if (row.vflex == 0) and (row.children.length > 0):
                    remainingHeight -= row.children[0].clientHeight
            
            # Apply height % for each flex row
            remainingPercentage = 100 * remainingHeight / table.clientHeight
            for i in range(len(table.children)):
                row = table.children[i]
                if row.vflex > 0:
                    row.style.height = round(row.vflex / cum_vflex * remainingPercentage) + 1 + '%'
    
    @js
    def _js_apply_cell_layout(self, row, col, vflex, hflex, cum_vflex, cum_hflex):
        raise NotImplementedError()



class FormLayout(BaseTableLayout):
    """ A form layout organizes pairs of widgets vertically.
    """
    
    CSS = """
    .flx-formlayout > tr > td > .flx-label {
        text-align: right;
    }
    """
    
    @js
    def _js_create_node(self):
        this.node = document.createElement('table')
        this.node.appendChild(document.createElement('tr'))
    
    @js
    def _js_add_child(self, widget):
        # Get row, create if necessary
        row = this.node.children[-1]
        itemsInRow = row.children.length
        if itemsInRow >= 2:
            row = document.createElement('tr')
            self.node.appendChild(row)
        # Create td and add widget to it
        td = document.createElement("td")
        row.appendChild(td)
        td.appendChild(widget.node)
        #
        self._update_layout()
        self._apply_table_layout()
        # do not call super!
    
    @js
    def _js_update_layout(self):
        """ Set hflex and vflex on node.
        """
        i = 0
        for widget in self.children:
            i += 1
            widget.node.hflex = 0 if (i % 2) else 1
            widget.node.vflex = widget.flex
        self._apply_table_layout()
    
    @js
    def _js_remove_child(self, widget):
        pass
        # do not call super!
    
    @js
    def _js_apply_cell_layout(self, row, col, vflex, hflex, cum_vflex, cum_hflex):
        AUTOFLEX = 729
        className = ''
        if (vflex == AUTOFLEX) or (vflex == 0):
            row.style.height = 'auto'
            className += ''
        else:
            row.style.height = vflex * 100 / cum_vflex + '%'
            className += 'vflex'
        className += ' '
        if (hflex == 0):
            col.style.width = 'auto'
            className += ''
        else:
            col.style.width = '100%'
            className += 'hflex'
        col.className = className


class GridLayout(BaseTableLayout):
    """ Not implemented.
    
    Do we even need it? If we do implement it, we need a way to specify
    the vertical flex value.
    """


class PinboardLayout(Layout):
    """ A layout that allows positiong child widgets at absolute and
    relative positions without constraining the widgets with respect to
    each-other.
    """
    
    CSS = """
    .flx-pinboardlayout-xxxxx {
        position: relative;
    }
    .flx-pinboardlayout > .flx-widget {
        position: absolute;
    }
    """
    
    @js
    def _js_create_node(self):
        this.node = document.createElement('div')


class Splitter(Layout):
    """ Abstract splitter class.
    """
    
    CSS = """
    .flx-splitter > .flx-splitter-container {
        /* width and heigth set by JS. This is a layout boundary 
        http://wilsonpage.co.uk/introducing-layout-boundaries/ */
        overflow: hidden;
        position: absolute;
        background: #fcc;
        top: 0px;
        left: 0px;    
    }
    
    .flx-hsplitter > .flx-splitter-container > .flx-widget {
        position: absolute;
        height: 100%;
    }
    .flx-vsplitter > .flx-splitter-container > .flx-widget {
        position: absolute;
        width: 100%;
    }
    
    .flx-hsplitter > .flx-splitter-container > .flx-splitter-divider, 
    .flx-hsplitter > .flx-splitter-container > .flx-splitter-handle {
        position: absolute;
        cursor: ew-resize;
        top: 0px;
        width: 6px; /* overridden in JS */
        height: 100%;
    }
    .flx-vsplitter > .flx-splitter-container > .flx-splitter-divider,
    .flx-vsplitter > .flx-splitter-container > .flx-splitter-handle {
        position: absolute;
        cursor: ns-resize;
        left: 0px;
        height: 6px; /* overridden in JS */
        width: 100%;
    }
    
    .dotransition > .flx-widget, .dotransition > .flx-splitter-divider {
        transition: left 0.3s, width 0.3s, right 0.3s;
    }
    
    .flx-splitter-divider {
        background: #eee;    
        z-index: 998;
    }
    
    .flx-splitter-handle {    
        background: none;    
        box-shadow:  0px 0px 12px #777;
        z-index: 999;
        transition: visibility 0.25s;
    }
    
    """
    
    @js
    def _js_create_node(self):
        this.node = document.createElement('div')
        
        # Add container. We need a container that is absolutely
        # positioned, because the children are positoned relative to
        # the first absolutely positioned parent.
        self._container = document.createElement('div')
        self._container.classList.add('flx-splitter-container')
        self.node.appendChild(self._container)
        
        # Add handle (the thing the user grabs and moves around)
        self._handle = document.createElement("div")
        self._handle.classList.add('flx-splitter-handle')
        self._container.appendChild(self._handle)
        self._handle.style.visibility = 'hidden'
        
        # Dividers are stored on their respective widgets, but we also keep
        # a list, which is synced by _js_ensure_all_dividers
        self._dividers = []
        self._setup()
    
    @js
    def _js_add_child(self, widget):
        self._insertWidget(widget, self.children.length - 1)
    
    @js
    def _js_remove_child(self, widget):
        
        clientWidth = 'clientWidth' if self._horizontal else 'clientHeight'
        sizeToDistribute = widget.node[clientWidth]
        
        # Remove widget
        self._container.removeChild(widget.node)
        # Remove its divider
        t = 0  # store divider position so we can fill the gap
        if widget._divider:
            t = widget._divider.t
            self._container.removeChild(widget._divider)
            del widget._divider
        
        # Update dividers (and re-index them)
        self._ensure_all_dividers()
        
        # Set new divider positions; distribute free space
        newTs = []
        tPrev = 0
        sizeFactor = self.node[clientWidth] / (self.node[clientWidth] - sizeToDistribute)
        
        for i in range(len(self.children)-1):
            divider = self.children[i]._divider
            curSize = divider.t - tPrev
            if tPrev < t and divider.t > t:
                curSize -= divider.t - t  # take missing space into account
            newTs.push(curSize * sizeFactor)
            tPrev = divider.t
            newTs[i] += newTs[i - 1] or 0
        
        for i in range(len(self._dividers)):
            self._move_divider(i, newTs[i])
        self._set_own_min_size()
    
    @js
    def _js_insertWidget(self, widget, index):
        """ Add to container and create divider if there is something
        to divide.
        """
        self._container.appendChild(widget.node)
        
        clientWidth = 'clientWidth' if self._horizontal else 'clientHeight'
        # children.splice(index, 0, widget.node);  -- done by our parenting system
        
        # Put a divider on all widgets except last, and index them
        self._ensure_all_dividers()
        
        # Set new divider positions; take space from each widget
        needSize = self.node[clientWidth] / self.children.length
        sizeFactor= (self.node[clientWidth] - needSize) / self.node[clientWidth]
        
        newTs = []
        tPrev = 0
        for i in range(len(self.children)-1):
            divider = self._dividers[i]
            if i == index:
                newTs.push(needSize)
            else:
                curSize = divider.t - tPrev
                newTs.push(curSize * sizeFactor)
                #print(index, i, t, self._dividers[i].t, curSize, newTs[i])
            tPrev = divider.t
            newTs[i] += newTs[i - 1] or 0
        
        #print(newTs + '', sizeLeft)
        for i in range(len(self.children)-1):
            self._move_divider(i, newTs[i])
        
        self._set_own_min_size()
    
    @js
    def _js_ensure_all_dividers(self):
        """ Ensure that all widgets have a divider object (except the last).
        Also update all divider indices, and dividers array.
        """
        width = 'width' if self._horizontal else 'height'
        clientWidth = 'clientWidth' if self._horizontal else 'clientHeight'
        
        self._dividers.length = 0  # http://stackoverflow.com/questions/1232040
        for i in range(len(self.children)-1):
            widget = self.children[i]
            if widget._divider is undefined:
                widget._divider = divider = document.createElement("div")
                divider.classList.add('flx-splitter-divider')
                divider.tInPerc = 1.0
                divider.style[width] = 2 * self._w2 + 'px'
                divider.t = self.node[clientWidth]
                self._container.appendChild(divider)
                self._connect_js_event(divider, 'mousedown', '_on_mouse_down')
            # Index
            widget._divider.index = i
            self._dividers.append(widget._divider)
        
        # Remove any dividers on the last widget
        if self.children:
            widget = self.children[-1]
            if widget._divider:
                self._container.removeChild(widget._divider)
                del widget._divider
    
    @js
    def _js_setup(self):
        """ Setup the splitter dynamics. We use closures that all access
        the same data.
        """
        handle = self._handle
        container = self._container
        that = this
        node = self.node
        dividers = self._dividers
        
        # Measure constants. We name these as if we have a horizontal
        # splitter, but the actual string might be the vertically
        # translated version.
        clientX = 'clientX' if self._horizontal else 'clientY'
        offsetLeft = 'offsetLeft' if self._horizontal else 'offsetTop'
        left = 'left' if self._horizontal else 'top'
        width = 'width' if self._horizontal else 'height'
        clientWidth = 'clientWidth' if self._horizontal else 'clientHeight'
        minWidth = 'min-width' if self._horizontal else 'min-height'
        minHeight = 'min-height' if self._horizontal else 'min-width'
        
        minimumWidth = 20
        w2 = 3  # half of divider width    
        handle.style[width] = 2 * w2 + 'px'
        
        # Flag to indicate dragging, the number indicates which divider is dragged (-1)
        handle.isdragging = 0
        
        def move_divider(i, t):
            # todo: make this publicly available?
            if t < 1:
                t *= node[clientWidth]
            t = clipT(i, t)
            # Store data
            dividers[i].t = t;
            dividers[i].tInPerc = t / node[clientWidth]  # to use during resizing
            # Set divider and handler
            handle.style[left] = dividers[i].style[left] = (t - w2) + 'px'
            # Set child widgets position on both sides of the divider
            begin = 0 if (i == 0) else dividers[i-1].t + w2
            end = node[clientWidth] if (i == len(dividers) - 1) else dividers[i+1].t - w2
            that.children[i].node.style[left] = begin + 'px'
            that.children[i].node.style[width] = (t - begin - w2) + 'px'
            that.children[i + 1].node.style[left] = (t + w2) + 'px'
            that.children[i + 1].node.style[width] = (end - t - w2) + 'px'
        
        def set_own_min_size():
            w = h = 50
            for i in range(len(that.children)):
                w += 2 * w2 + parseFloat(that.children[i].node.style[minWidth]) or minimumWidth
                h = max(h, parseFloat(that.children[i].node.style[minHeight]))
            # node.style[minWidth] = w + 'px'
            # node.style[minHeight] = h + 'px'
        
        def clipT(i, t):
            """ Clip the t value, taking into account the boundary of the 
            splitter itself, neighboring dividers, and the minimum sizes 
            of widget elements.
            """
            # Get min and max towards edges or other dividers
            min = dividers[i - 1].t if (i > 0) else 0
            max = dividers[i + 1].t if (i < dividers.length - 1) else node[clientWidth]
            # Take minimum width of widget into account
            # todo: this assumes the minWidth is specified in pixels, not e.g em.
            min += 2 * w2 + parseFloat(that.children[i].node.style[minWidth]) or minimumWidth
            max -= 2 * w2 + parseFloat(that.children[i + 1].node.style[minWidth]) or minimumWidth
            # Clip
            return Math.min(max, Math.max(min, t))
        
        def on_resize(event):
            # Keep container in its max size
            # No need to take splitter orientation into account here
            container.style.left = node.offsetLeft + 'px'
            container.style.top = node.offsetTop + 'px'
            #container.style.width = node.clientWidth + 'px'
            #container.style.height = node.clientHeight + 'px'
            container.style.width = node.offsetWidth + 'px'
            container.style.height = node.offsetHeight + 'px'
            container.classList.remove('dotransition')
            for i in range(len(dividers)):
                move_divider(i, dividers[i].tInPerc)
        
        def on_mouse_down(ev):
            container.classList.add('dotransition')
            ev.stopPropagation()
            ev.preventDefault()
            handle.isdragging = ev.target.index + 1
            move_divider(ev.target.index, ev[clientX] - node[offsetLeft])
            handle.style.visibility = 'visible'
        
        def on_mouse_move(ev):
            if handle.isdragging:
                ev.stopPropagation()
                ev.preventDefault()
                i = handle.isdragging - 1
                x = ev[clientX] - node[offsetLeft] - w2
                handle.style[left] = clipT(i, x) + 'px'
        
        def on_mouse_up(ev):
            if handle.isdragging:
                ev.stopPropagation()
                ev.preventDefault()
                i = handle.isdragging - 1
                handle.isdragging = 0;
                handle.style.visibility = 'hidden'
                move_divider(i, clipT(i, ev[clientX] - node[offsetLeft]))
        
        # Make available as method
        self._set_own_min_size = set_own_min_size
        self._move_divider = move_divider
        self._on_mouse_down = on_mouse_down
        
        # Connect events
        self.connect_event('resize', on_resize)
        container.addEventListener('mousemove', on_mouse_move, False)
        window.addEventListener('mouseup', on_mouse_up, False)
        # todo: does JS support mouse grabbing?


class HSplitter(Splitter):
    """ The HSplitter widget divides the available horizontal space
    among its child widgets in a similar way that the HBox does, except
    in this case the user can divide the space by dragging the divider
    in between the widgets.
    """
    
    @js
    def _js_init(self):
        self._horizontal = True
        super()._init()
        

class VSplitter(Splitter):
    """ The VSplitter widget divides the available vertical space
    among its child widgets in a similar way that the VBox does, except
    in this case the user can divide the space by dragging the divider
    in between the widgets.
    """
    
    @js
    def _js_init(self):
        self._horizontal = False
        super()._init()
