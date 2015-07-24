""" Layout widgets
"""

from ..pyscript import js
from .. import react

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


class Box(Layout):
    """ Abstract class for HBox and VBox.
    
    Child widgets are tiled either horizontally or vertically. The space
    that each widget takes is determined by its minimal required size
    and the flex value of each widget.
    
    Example:
    
    .. UIExample:: 200
        
        from flexx import ui
        
        class App(ui.App):
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
                    
                    ui.Label(text='margin 10 (around layout)')
                    with ui.HBox(flex=0, margin=10):
                        self.b1 = ui.Button(text='Hola', flex=1)
                        self.b2 = ui.Button(text='Hello world', flex=1)
                        self.b3 = ui.Button(text='Foo bar', flex=1)
                    
                    ui.Label(text='spacing 10 (inter-widget)')
                    with ui.HBox(flex=0, spacing=10):
                        self.b1 = ui.Button(text='Hola', flex=1)
                        self.b2 = ui.Button(text='Hello world', flex=1)
                        self.b3 = ui.Button(text='Foo bar', flex=1)
                    
                    ui.Widget(flex=1)
                    ui.Label(text='Note the spacer Widget above')
    
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
    
    /*
    .box-align-center { -webkit-align-items: center; -ms-align-items: center; -moz-align-items: center; align-items: center; }
    .box-align-center { -webkit-align-items: center; -ms-align-items: center; -moz-align-items: center; align-items: center; }
    */
    
    /* Make child widgets (and layouts) size correctly */
    .flx-hbox > .flx-widget {
        height: 100%;
        width: auto;
    }
    .flx-vbox > .flx-widget {
        width: 100%;
        height: auto;
    }
    """
    
    @react.input
    def margin(v=0):
        """ The empty space around the layout. """
        return float(0)
    
    @react.input
    def spacing(v=0):
        """ The space between two child elements. """
        return float(0)
    
    class JS:
    
        def _create_node(self):
            this.node = document.createElement('div')
        
        @react.act('children.*.flex')
        def _set_flexes(*flexes):
            for widget in self.children():
                # todo: make flex 2D?
                self._applyBoxStyle(widget.node, 'flex-grow', widget.flex())
        
        @react.act('spacing', 'children')
        def _spacing_changed(self, spacing, children):
            if children.length:
                children[0].node.style['margin-left'] = '0px'
                for child in children[1:]:
                    child.node.style['margin-left'] = spacing + 'px'
        
        @react.act('margin')
        def _margin_changed(self, margin):
            self.node.style['padding'] = margin + 'px'


class HBox(Box):
    """ Layout widget to distribute elements horizontally.
    See :doc:`Box` for more info.
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
    
    class JS:
        def _init(self):
            super()._init()
            # align-items: flex-start, flex-end, center, baseline, stretch
            self._applyBoxStyle(self.node, 'align-items', 'center')
            #justify-content: flex-start, flex-end, center, space-between, space-around
            self._applyBoxStyle(self.node, 'justify-content', 'space-around')


class VBox(Box):
    """ Layout widget to distribute elements vertically.
    See :doc:`Box` for more info.
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
    
    class JS:
        def _init(self):
            super()._init()
            self._applyBoxStyle(self.node, 'align-items', 'stretch')
            self._applyBoxStyle(self.node, 'justify-content', 'space-around')


class BaseTableLayout(Layout):
    """ Abstract base class for layouts that use an HTML table.
    
    Layouts that use this approach are rather bad in performance when
    resizing. This is not so much a problem when it is a leaf layout,
    but we don't recommend embedding such layouts in each-other.
    """
    
    CSS = """
    
    /* Clear any styling on this table (rendered_html is an IPython thing) */
    .flx-basetablelayout, .flx-basetablelayout td, .flx-basetablelayout tr,
    .rendered_html .flx-basetablelayout {
        border: 0px;
        padding: initial;
        margin: initial;
        background: initial;
    }
    
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
    
    class JS:
        
        def _apply_table_layout(self):
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
        
        @react.act('real_size')
        def _adapt_to_size_change(self, size):
            """ This function adapts the height (in percent) of the flexible rows
            of a layout. This is needed because the percent-height applies to the
            total height of the table. This function is called whenever the
            table resizes, and adjusts the percent-height, taking the available 
            remaining table height into account. This is not necesary for the
            width, since percent-width in colums *does* apply to available width.
            """
            table = self.node  # or event.target
            #print('heigh changed', event.heightChanged, event.owner.__id)
            
            if not self.real_size.last_value or (self.real_size.value[1] !=
                                                 self.real_size.last_value[1]):
                
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
        
        def _apply_cell_layout(self, row, col, vflex, hflex, cum_vflex, cum_hflex):
            raise NotImplementedError()



class FormLayout(BaseTableLayout):
    """ A form layout organizes pairs of widgets vertically.
    
    Note: the API may change. maybe the label can be derived from the
    widgets' ``title`` property?
    
    Example:
    
    .. UIExample:: 200
        
        from flexx import ui
        
        class App(ui.App):
            def init(self):
                with ui.FormLayout():
                    ui.Label(text='Pet name:')
                    self.b1 = ui.Button(text='...')
                    ui.Label(text='Pet Age:')
                    self.b2 = ui.Button(text='...')
                    ui.Label(text="Pet's Favorite color:")
                    self.b3 = ui.Button(text='...')
                    ui.Widget(flex=1)
    """
    
    CSS = """
    .flx-formlayout > tr > td > .flx-label {
        text-align: right;
    }
    """
    
    class JS:
        
        def _create_node(self):
            this.node = document.createElement('table')
            this.node.appendChild(document.createElement('tr'))
        
        def _add_child(self, widget):
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
        
        def _update_layout(self):
            """ Set hflex and vflex on node.
            """
            i = 0
            for widget in self.children():
                i += 1
                widget.node.hflex = 0 if (i % 2) else 1
                widget.node.vflex = widget.flex()
            self._apply_table_layout()
        
        def _remove_child(self, widget):
            pass
            # do not call super!
        
        def _apply_cell_layout(self, row, col, vflex, hflex, cum_vflex, cum_hflex):
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


# todo: rename? this is called FloatLayout in Kivy
class PinboardLayout(Layout):
    """ A layout that allows positiong child widgets at absolute and
    relative positions without constraining the widgets with respect to
    each-other.
    
    Example:
    
    .. UIExample:: 200
        
        from flexx import ui
        
        class App(ui.App):
            def init(self):
                with ui.PinboardLayout():
                    self.b1 = ui.Button(text='Stuck at (20, 20)', pos=(20, 30))
                    self.b2 = ui.Button(text='Dynamic at (30%, 30%)', pos=(0.3, 0.3))
                    self.b3 = ui.Button(text='Dynamic at (50%, 70%)', pos=(0.5, 0.7))

    """
    
    CSS = """
    .flx-pinboardlayout-xxxxx {
        position: relative;
    }
    .flx-pinboardlayout > .flx-widget {
        position: absolute;
    }
    """
    
    class JS:
        def _create_node(self):
            this.node = document.createElement('div')


class Splitter(Layout):
    """ Abstract splitter class.
    
    The HSplitter  and VSplitter layouts divide the available space
    among its child widgets in a similar way that HBox and VBox do,
    except that the user can divide the space by dragging the
    divider in between the widgets.
    
    Due to constraints of JavaScript, the natural size of child widgets
    cannot be taken into account. However, the minimum size of child
    widgets *is* taken into account, and the splitter also sets its own
    minimum size accordingly.
    
    Example:
    
    .. UIExample:: 200
        
        from flexx import ui
        
        class App(ui.App):
            def init(self):
                with ui.HSplitter():
                    ui.Button(text='Left A')
                    with ui.VSplitter():
                        ui.Button(text='Right B')
                        ui.Button(text='Right C')
                        ui.Button(text='Right D')
    
    """
    
    CSS = """
    
    /* Behave nice in the notebook */
    /* todo: give all widgets min-height property that is 20px for hslitter and 50 for vsplitter */
    .flx-container > .flx-hsplitter {
       min-height: 30px;
    }
    .flx-container > .flx-vsplitter {
       min-height: 200px;
    }
    
    /* Make child widget size ok */
    .flx-hsplitter > .flx-splitter-container > .flx-widget {
        width: auto;
        height: 100%;
    }
    .flx-vsplitter > .flx-splitter-container > .flx-widget {
        height: auto;
        width: 100%;
    }
    
    flx-splitter-container > .flx-splitter {
        height: auto;
        width: auto;
    }
    
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
    
    /* this does not work well with keeping resize events propagation
    .dotransition > .flx-widget, .dotransition > .flx-splitter-divider {
        transition: left 0.3s, width 0.3s, right 0.3s;
    }
    */
    
    .flx-splitter-divider {
        background: #eee;    
        z-index: 998;
    }
    
    .flx-splitter-handle {    
        background: none;    
        box-shadow:  0px 0px 12px #777;
        z-index: 999;
        opacity: 0;
        pointer-events: none;
        transition: opacity 0.5s;
    }
    
    """
    
    class JS:
        
        def _create_node(self):
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
            #self._handle.style.visibility = 'hidden'
            self._handle.style.opacity = '0'
            
            # Dividers are stored on their respective widgets, but we also keep
            # a list, which is synced by _js_ensure_all_dividers
            self._dividers = []
            self._setup()
        
        def _add_child(self, widget):
            self._insertWidget(widget, self.children().length - 1)
        
        def _remove_child(self, widget):
            
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
            
            for i in range(len(self.children())-1):
                divider = self.children()[i]._divider
                curSize = divider.t - tPrev
                if tPrev < t and divider.t > t:
                    curSize -= divider.t - t  # take missing space into account
                newTs.push(curSize * sizeFactor)
                tPrev = divider.t
                newTs[i] += newTs[i - 1] or 0
            
            for i in range(len(self._dividers)):
                self._move_divider(i, newTs[i])
            self._set_own_min_size()
        
        def _insertWidget(self, widget, index):
            """ Add to container and create divider if there is something
            to divide.
            """
            self._container.appendChild(widget.node)
            children = self.children()
            
            clientWidth = 'clientWidth' if self._horizontal else 'clientHeight'
            # children.splice(index, 0, widget.node);  -- done by our parenting system
            
            # Put a divider on all widgets except last, and index them
            self._ensure_all_dividers()
            
            # Set new divider positions; take space from each widget
            needSize = self.node[clientWidth] / children.length
            sizeFactor= (self.node[clientWidth] - needSize) / self.node[clientWidth]
            
            newTs = []
            tPrev = 0
            for i in range(len(children)-1):
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
            for i in range(len(children)-1):
                self._move_divider(i, newTs[i])
            
            self._set_own_min_size()
        
        def _ensure_all_dividers(self):
            """ Ensure that all widgets have a divider object (except the last).
            Also update all divider indices, and dividers array.
            """
            width = 'width' if self._horizontal else 'height'
            clientWidth = 'clientWidth' if self._horizontal else 'clientHeight'
            children = self.children()
            
            self._dividers.length = 0  # http://stackoverflow.com/questions/1232040
            for i in range(len(children)-1):
                widget = children[i]
                if widget._divider is undefined:
                    widget._divider = divider = document.createElement("div")
                    divider.classList.add('flx-splitter-divider')
                    divider.tInPerc = 1.0
                    divider.style[width] = 2 * self._w2 + 'px'
                    divider.t = self.node[clientWidth]
                    self._container.appendChild(divider)
                    divider.addEventListener('mousedown', self._on_mouse_down, False)
                # Index
                widget._divider.index = i
                self._dividers.append(widget._divider)
            
            # Remove any dividers on the last widget
            if len(children):
                widget = children[-1]
                if widget._divider:
                    self._container.removeChild(widget._divider)
                    del widget._divider
        
        def _setup(self):
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
                children = that.children()
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
                children[i].node.style[left] = begin + 'px'
                children[i].node.style[width] = (t - begin - w2) + 'px'
                children[i + 1].node.style[left] = (t + w2) + 'px'
                children[i + 1].node.style[width] = (end - t - w2) + 'px'
                # We resized our children
                children[i]._check_resize()
                children[i+1]._check_resize()
            
            def set_own_min_size():
                w = h = 50
                children = that.children()
                for i in range(len(children)):
                    w += 2 * w2 + parseFloat(children[i].node.style[minWidth]) or minimumWidth
                    h = max(h, parseFloat(children[i].node.style[minHeight]))
                node.style[minWidth] = w + 'px'
                node.style[minHeight] = h + 'px'
            
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
                min += 2 * w2 + parseFloat(that.children()[i].node.style[minWidth]) or minimumWidth
                max -= 2 * w2 + parseFloat(that.children()[i + 1].node.style[minWidth]) or minimumWidth
                # Clip
                return Math.min(max, Math.max(min, t))
            
            def on_resize():
                # Keep container in its max size
                # No need to take splitter orientation into account here
                if window.getComputedStyle(node).position == 'absolute':
                    container.style.left = '0px'
                    container.style.top = '0px'
                    container.style.width = node.offsetWidth + 'px'
                    container.style.height = node.offsetHeight + 'px'
                else:
                    # container.style.left = node.clientLeft + 'px'
                    # container.style.top = node.clientTop + 'px'
                    # container.style.width = node.clientWidth + 'px'
                    # container.style.height = node.clientHeight + 'px'
                    container.style.left = node.offsetLeft + 'px'
                    container.style.top = node.offsetTop + 'px'
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
                handle.mouseStartPos = ev[clientX]
                #x = ev[clientX] - node.getBoundingClientRect().x - w2
                #move_divider(ev.target.index, x)
                #handle.style.visibility = 'visible'
                handle.style.opacity = '1'
            
            def on_mouse_move(ev):
                if handle.isdragging:
                    ev.stopPropagation()
                    ev.preventDefault()
                    i = handle.isdragging - 1
                    x = ev[clientX] - node.getBoundingClientRect().x - w2
                    handle.style[left] = clipT(i, x) + 'px'
            
            def on_mouse_up(ev):
                if handle.isdragging:
                    ev.stopPropagation()
                    ev.preventDefault()
                    i = handle.isdragging - 1
                    handle.isdragging = 0;
                    #handle.style.visibility = 'hidden'
                    handle.style.opacity = '0'
                    x = ev[clientX] - node.getBoundingClientRect().x
                    move_divider(i, clipT(i, x))
            
            # Make available as method
            self._set_own_min_size = set_own_min_size
            self._move_divider = move_divider
            self._on_mouse_down = on_mouse_down
            self._on_resize = on_resize
            print('on_resize set')
            
            # Connect events
            container.addEventListener('mousemove', on_mouse_move, False)
            window.addEventListener('mouseup', on_mouse_up, False)
            # todo: does JS support mouse grabbing?
        
        @react.act('real_size')
        def _resize_elements(self, size):
            if self._on_resize:  # todo: WTF, is this not alwyas supposed to be there?
                self._on_resize()


class HSplitter(Splitter):
    """ Horizontal splitter.
    See :doc:`Splitter` for more information.
    """
    
    class JS:
        def _init(self):
            self._horizontal = True
            super()._init()


class VSplitter(Splitter):
    """ Vertical splitter.
    See :doc:`Splitter` for more information.
    """
    
    class JS:
        def _init(self):
            self._horizontal = False
            super()._init()
