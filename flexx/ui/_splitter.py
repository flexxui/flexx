"""
The splitter layout classes provide a mechanism to horizontally
or vertically stack child widgets, where the available space can be
manually specified by the user.

Example:

.. UIExample:: 200
    
    from flexx import ui
    
    class Example(ui.Widget):
        def init(self):
            with ui.HSplitter():
                ui.Button(text='Left A')
                with ui.VSplitter():
                    ui.Button(text='Right B')
                    ui.Button(text='Right C')
                    ui.Button(text='Right D')
"""

from .. import react
from . import Widget, Layout


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
        
        @react.connect('real_size')
        def _resize_elements(self, size):
            if self._on_resize:  # todo: WTF, is this not alwyas supposed to be there?
                self._on_resize()


class HSplitter(Splitter):
    """ Horizontal splitter.
    See Splitter for more information.
    """
    
    class JS:
        def _init(self):
            self._horizontal = True
            super()._init()


class VSplitter(Splitter):
    """ Vertical splitter.
    See Splitter for more information.
    """
    
    class JS:
        def _init(self):
            self._horizontal = False
            super()._init()
