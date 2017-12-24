"""
.. UIExample:: 100

    from flexx import app, ui

    class Example(ui.Widget):
        ''' A red widget '''
        CSS = ".flx-Example {background:#f00; min-width:20px; min-height:20px;}"

"""

from ..event import loop
from .. import event, app
from ..pyscript import undefined, window, this_is_js

from . import logger  # noqa


# todo: move to flexx.event.properties?
class FloatPairProp(event.Property):
    """ A property that represents a pair of float values, which can also be
    set using a scalar.
    """
    
    _default = (0, 0)
    
    def _validate(self, value):
        if not isinstance(value, (tuple, list)):
            value = value, value
        if not len(value) == 2:
            raise TypeError('FloatPair property needs a scalar '
                            'or two values, not %i' % len(value))
        if not (isinstance(value[0], (int, float)) or isinstance(value[0], str)):
            raise TypeError('FloatPair 1st value cannot be %r.' % value[0])
        if not (isinstance(value[1], (int, float)) or isinstance(value[1], str)):
            raise TypeError('FloatPair 2nd value cannot be %r.' % value[1])
        value = float(value[0]), float(value[1])
        if this_is_js():  # pragma: no cover
            # Cripple the object so in-place changes are harder. Note that we
            # cannot prevent setting or deletion of items.
            value.push = undefined
            value.splice = undefined
            value.push = undefined
            value.reverse = undefined
            value.sort = undefined
        return value


class Widget(app.JsComponent):
    """ Base widget class.

    When *subclassing* a Widget to create a compound widget (a widget
    that acts as a container for other widgets), use the ``init()``
    method to initialize the child widgets. This method is called while
    the widget is the current widget. 
    """

    CSS = """

    .flx-Widget {
        box-sizing: border-box;
        overflow: hidden;
        position: relative;  /* helps with absolute positioning of content */
    }
    
    /* in a notebook or otherwise embedded in classic HTML */
    .flx-container {
        min-height: 20px;
    }
    
    /* Main widget to fill the whole page */
    .flx-main-widget {
       position: absolute;
       left: 0;
       right: 0;
       width: 100%;
       top: 0;
       bottom: 0;
       height: 100%;
    }
    
    /* to position children absolute */
    .flx-abs-children > .flx-Widget {
        position: absolute;
    }
    
    /* Fix issue flexbox > Widget > layout on Chrome */
    .flx-Widget:not(.flx-Layout) > .flx-Layout {
        position: absolute;
    }
    """
    
    ## Properties
    
    container = event.StringProp('', settable=True, doc="""
        The id of the DOM element that contains this widget if
        parent is None. Use 'body' to make this widget the root.
        """)
    
    parent = event.ComponentProp(None, doc="""
        The parent widget, or None if it has no parent. Setting
        this property will update the "children" property of the
        old and new parent.
        """)
        
    children = app.LocalProperty((), doc="""
        The child widgets of this widget. This property is not settable and
        only present in JavaScript.
        """)
    
    title = event.StringProp('', settable=True, doc="""
        The string title of this widget. This is used to mark
        the widget in e.g. a tab layout or form layout, and is used
        as the app's title if this is the main widget.
        """)
    
    icon = event.StringProp('', settable=True, doc="""
        The icon for this widget. This is used is some widgets classes,
        and is used as the app's icon if this is the main widget.
        
        Can be a url, a relative url to a shared asset, or a base64
        encoded image. In the future this may also support names in
        icon packs like fontaweome.
        """)
    
    css_class = event.StringProp('', settable=True, doc="""
        The extra CSS class name to asign to the DOM element.
        Spaces can be used to delimit multiple names. Note that the
        DOM element already has a css class-name corresponding to
        its class (e.g. 'flx-Widget) and all its superclasses.
        """)
    
    flex = FloatPairProp((0, 0), settable=True, doc="""
        How much space this widget takes (relative to the other
        widgets) when contained in a flexible layout such as BoxLayout,
        BoxPanel, FormLayout or GridPanel. A flex of 0 means to take
        the minimum size. Flex is a two-element tuple, but both values
        can be specified at once by specifying a scalar.
        """)
        # todo: make a custom 2Tuple prop to allow specifying as scalar, also pos and size etc
    
    # todo: PinBoardLayout and GridPanel or not used a lot, deprecate?
    pos = FloatPairProp((0, 0), settable=True, doc="""
        The position of the widget when it is in a layout that allows
        positioning, this can be an arbitrary position (e.g. in
        PinBoardLayout) or the selection of column and row in a
        GridPanel.
        """)
    
    base_size = FloatPairProp((32, 32), settable=True, doc="""
        The given size of the widget when it is in a layout that
        allows explicit sizing, or the base-size in a BoxPanel or
        GridPanel.
        """)
    
    size = FloatPairProp((0, 0), settable=False, doc="""
        The actual size of the widget. Flexx tries to keep this value
        up-to-date, but in e.g. a box layout, a change in a Button's
        text can change the size of sibling widgets.
        """)
    
    size_min_max = event.TupleProp((0, 1e9, 0, 1e9), settable=False, doc="""
        A 4-element tuple (min-width, max-width, min-height, max-height)
        derived from the element's style, in pixels.
        """)
    
    # todo: turn this into an intProp None->-2?
    # Also see size readonly defined in JS
    tabindex = event.AnyProp(None, settable=True, doc="""
        The index used to determine widget order when the user
        iterates through the widgets using tab. This also determines
        if a widget is able to receive key events. Flexx automatically
        sets this property when it should emit key events.
        Effect of possible values on underlying DOM element:
        
        * None: element cannot have focus unless its a special element like
            a link or form control (default).
        * -1: element can have focus, but is not reachable via tab.
        * 0: element can have focus, and is reachable via tab in the order
            at which the element is defined.
        * 1 and up: element can have focus, and the tab-order is determined
            by the value of tabindex.
        """)
    
    ## Methods
    
    def __init__(self, *init_args, **kwargs):

        # Handle parent
        parent = kwargs.pop('parent', None)
        if parent is None:
            active_component = loop.get_active_component()
            if isinstance(active_component, Widget):
                parent = active_component
        # -> we apply via set_parent below
        
        # Use parent session unless session was given
        if parent is not None and not kwargs.get('flx_session', None):
            kwargs['flx_session'] = parent.session
        
        # todo: document this
        style = kwargs.pop('style', '')
        
        # todo: it seems like we can get rid of this is_app thing
        # if kwargs.get('is_app', False):
        #     kwargs['container'] = 'body'
        
        # Init this component (e.g. create properties and actions)
        super().__init__(*init_args, **kwargs)
        # Now we can initialize further ...
        
        # Attach this widget in the widget hierarchy, if we can
        if parent is not None:
            # Just attach to the parent
            self.set_parent(parent)
        elif self.container == '':
            # Determine whether this should be the main widget. If the browser
            # seems to need one, and this is the first "orphan" widget to be 
            # instantiated, this widget will take on this role.
            if window.flexx.need_main_widget:
                window.flexx.need_main_widget = False
                self.set_container('body')
        
        # Create DOM nodes
        # todo: how does_render() fit into this?
        self._init_dom()
        
        # Derive css class name from class hierarchy
        cls = self.__class__
        for i in range(32):  # i.e. a safe while-loop
            self.outernode.classList.add('flx-' + cls.__name__)
            if cls is Widget.prototype:
                break
            cls = cls._base_class
        else:
            raise RuntimeError('Error determining class names for %s' % self.id)
        
        if style:
            self.apply_style(style)
        self._check_min_max_size()
        
        # Setup JS events to enter Flexx' event system
        self._init_events()
    
    def init(self):
        """ Overload this to initialize a custom widget. When called, this
        widget is the current parent.
        """
        # The Component class already implement a stub, but we may like a more
        # specific docstring here.
        pass
    
    def _init_dom(self):
        """ Initialize DOM nodes for this widget. Overload in subclasses.
        """
        self.node = window.document.createElement('div')
        self.outernode = self.node
    
    # todo: mmm, need this at the Python side
    def _repr_html_(self):
        """ This is to get the widget shown inline in the notebook.
        """
        if self.container:
            return "<i>This widget is already shown in this notebook</i>"

        container_id = self.id + '_container'
        self.set_container(container_id)
        return "<div class='flx-container' id=%s />" % container_id

    def dispose(self):
        """ Overloaded version of dispose() that disposes any child widgets.
        """
        # Dispose children? Yes, each widget can have exactly one parent and
        # when that parent is disposed, it makes sense to assume that the
        # child ought to be disposed as well. It avoids memory leaks. If a
        # child is not supposed to be disposed, the developer should orphan the
        # child widget.
        children = self.children
        # First dispose children (so they wont send messages back), then clear
        # the children and dispose ourselves.
        for child in children:
            child.dispose()
        super().dispose()
        self.set_parent(None)
        self._children_value = ()
    
    # @event.connect('parent:aaa')
    # def __keep_alive(self, *events):
    #     # When the parent changes, we prevent the widget from being deleted
    #     # for a few seconds, to it will survive parent-children "jitter".
    #     self._session.keep_alive(self)
    # todo: not necessary because we keep_alive when a Component is send over, or is that too heavy?
    
    
    ## Actions
    
    
    @event.action
    def apply_style(self, style):
        """ Apply CSS style to this widget object. e.g.
        ``"background: #f00; color: #0f0;"``. If the given value is a
        dict, its key-value pairs are converted to a CSS style string.
        
        For static styling it is often better to define a CSS class attribute
        and/or use ``css_class``.
        """
        if isinstance(style, dict):
            style = ['%s: %s' % (k, v) for k, v in style.items()]
            style = '; '.join(style)
        
        # self.node.style = style  # forbidden in strict mode,
        # plus it clears all previously set style

        # Note that styling is applied to the outer node, just like
        # the styling defined via the CSS attribute. In most cases
        # the inner and outer node are the same, but not always
        # (e.g. CanvasWidget).

        # Set style elements, keep track in a dict
        d = {}
        if style:
            for part in style.split(';'):
                if ':' in part:
                    key, val = part.split(':')
                    key, val = key.trim(), val.trim()
                    self.outernode.style[key] = val
                    d[key] = val

        # Did we change style related to sizing?
        size_limits_keys = 'min-width', 'min-height', 'max-width', 'max-height'
        size_limits_changed = False
        for key in size_limits_keys:
            if key in d:
                size_limits_changed = True
        
        if size_limits_changed:
             self._check_min_max_size()
    
    ## Reactions
    
    @event.reaction('css_class')
    def __css_class_changed(self, *events):
        if len(events):
            # Reset / apply explicitly given class name (via the prop)
            for cn in events[0].old_value.split(' '):
                if cn:
                    self.outernode.classList.remove(cn)
            for cn in events[-1].new_value.split(' '):
                if cn:
                    self.outernode.classList.add(cn)
    
    @event.reaction('title')
    def __title_changed(self, *events):
        if self.parent is None and self.container == 'body':
            window.document.title = self.title or 'Flexx app'
    
    @event.reaction('icon')
    def __icon_changed(self, *events):
        if self.parent is None and self.container == 'body':
            window.document.title = self.title or 'Flexx app'
            
            link = window.document.createElement('link')
            oldLink = window.document.getElementById('flexx-favicon')
            link.id = 'flexx-favicon'
            link.rel = 'shortcut icon'
            link.href = events[-1].new_value
            if oldLink:
                window.document.head.removeChild(oldLink)
            window.document.head.appendChild(link)
    
    @event.reaction('tabindex')
    def __update_tabindex(self, *events):
        # Note that this also makes the widget able to get focus, and thus
        # able to do key events.
        ti = events[-1].new_value
        if ti is None:
            self.node.removeAttribute('tabIndex')
        else:
            self.node.tabIndex = ti
    
    # Now solved with CSS, which seems to work, but leaving this code for now ...
    # @event.reaction('children', '!children*.mode', '!children*.orientation')
    # def __make_singleton_container_widgets_work(self, *events):
    #     classNames = self.outernode.classList
    #     if not classNames.contains('flx-Layout'):
    #         # classNames.remove('flx-box')
    #         # classNames.remove('flx-horizontal')
    #         # classNames.remove('flx-vertical')
    #         classNames.remove('flx-abs-children')
    #         children = self.children
    #         if len(children) == 1:
    #             subClassNames = children[0].outernode.classList
    #             if subClassNames.contains('flx-Layout'):
    #                 classNames.add('flx-abs-children')
    #             # This seems to be enough, though previously we did:
    #             # if subClassNames.contains('flx-box'):
    #             #     # classNames.add('flx-box')
    #             #     vert = subClassNames.contains('flx-vertical')
    #             #     classNames.add('flx-horizontal' if vert else 'flx-horizontal')
    #             # else:
    #             #     # If child is a layout that uses absolute position, make
    #             #     # out children absolute.
    #             #     for name in ('split', 'StackPanel', 'TabPanel', 'DockPanel'):
    #             #         if subClassNames.contains('flx-' + name):
    #             #             classNames.add('flx-abs-children')
    #             #             break
    
    ## Sizing
    
    @event.action
    def check_real_size(self):
        """ Check whether the current size has changed. It should usually not
        be necessary to invoke this action, since a widget does so by itself,
        but it some situations the widget may not be aware of possible size
        changes.
        """
        n = self.outernode
        cursize = self.size
        if cursize[0] != n.clientWidth or cursize[1] != n.clientHeight:
            self._mutate_size([n.clientWidth, n.clientHeight])
    
    @event.action
    def _check_min_max_size(self):
        """ Query the minimum and maxium size.
        """
        mima = self._query_min_max_size()
        self._mutate_size_min_max(mima)
    
    def _query_min_max_size(self):
        # Query
        style = window.getComputedStyle(self.outernode)
        mima = [style.minWidth, style.maxWidth, style.minHeight, style.maxHeight]
        # Pixelize - we dont handle % or em or whatever
        for i in range(4):
            if mima[i] == '0':
                mima[i] = 0
            elif mima[i].endswith('px'):
                mima[i] = float(mima[i][:-2])
            else:
                mima[i] = 0 if (i == 0 or i == 2) else 1e9
        # Protect against min > max
        if mima[0] > mima[1]:
            mima[0] = mima[1] = 0.5 * (mima[0] + mima[1])
        if mima[2] > mima[3]:
            mima[2] = mima[3] = 0.5 * (mima[2] + mima[3])
        return mima
    
    @event.reaction('children', 'children*.size_min_max')
    def __min_max_size_may_have_changed(self, *events):
        self._check_min_max_size()
    
    @event.reaction('container', 'parent.size', 'children')
    def __size_may_have_changed(self, *events):
        # Invoke actions, i.e. check size in *next* event loop iter to
        # give the DOM a chance to settle.
        self.check_real_size()
    
    def _set_size(self, prefix, w, h):
        """ Method to allow setting size (via style). Used by some layouts.
        """
        size = w, h
        for i in range(2):
            if size[i] <= 0 or size is None or size is undefined:
                size[i] = ''  # Use size defined by CSS
            elif size[i] > 1:
                size[i] = size[i] + 'px'
            else:
                size[i] = size[i] * 100 + '%'
        self.outernode.style[prefix + 'width'] = size[0]
        self.outernode.style[prefix + 'height'] = size[1]
    
    ## Parenting
    
    @event.action
    def set_parent(self, parent, pos=None):
        """ Set the parent widget (can be None). This action also mutates the
        childen of the old and new parent.
        """
        old_parent = self.parent  # or None
        new_parent = parent
        
        # Early exit
        if new_parent is old_parent and pos is None:
            return
        if not (new_parent is None or isinstance(new_parent, Widget)):
            raise ValueError('%s.parent must be a Widget or None' % self.id)
        
        # Apply parent
        self._mutate_parent(new_parent)
        
        # Remove ourselves
        if old_parent is not None:
            children = list(old_parent.children)
            while self in children:
                children.remove(self)
            if old_parent is not new_parent:
                old_parent._mutate_children(children)
        
        # Insert ourselves
        if new_parent is not None:
            if old_parent is not new_parent: 
                children = list(new_parent.children)
            while self in children:
                children.remove(self)
            if pos is None:
                children.append(self)
            elif pos >= 0:
                children.insert(pos, self)
            elif pos < 0:
                children.append(None)
                children.insert(pos, self)
                children.pop(-1)
            else:  # maybe pos is nan for some reason
                children.append(None)
            new_parent._mutate_children(children)
    
    @event.reaction('container')
    def __container_changed(self, *events):
        id = events[-1].new_value
        self.outernode.classList.remove('flx-main-widget')
        if self.parent:
            return
        
        # Let session keep us up to date about size changes
        self._session.keep_checking_size_of(self, bool(id))
        
        if id:
            if id == 'body':
                el = window.document.body
                self.outernode.classList.add('flx-main-widget')
                window.document.title = self.title or 'Flexx app'
            else:
                el = window.document.getElementById(id)
            el.appendChild(self.outernode)
    
    @event.reaction('children')
    def __children_changed(self, *events):
        """ Make child widgets appear (in the right order) in a layout.
        """
        self._update_layout(events[0].old_value, events[-1].new_value)
    
    def _update_layout(self, old_children, new_children):
        """ Can be overloaded in (Layout) subclasses.
        """
        for w in old_children:
            self.node.removeChild(w.outernode)
        for w in new_children:
            self.node.appendChild(w.outernode)
    
    ## Events

    # todo: events: focus, enter, leave ... ?
    
    # todo: document this hook-like class attribute
    CAPTURE_MOUSE = False
    
    # def _new_event_type_hook(self, event_type):
    #     # In order to receive JS key events, we need a tabindex.
    #     if self.tabindex is None:
    #         if event_type in ('key_down', 'key_up', 'key_press'):
    #             self.tabindex = -1
    #     super()._new_event_type_hook(event_type)
    
    # todo: verify that the below correctly replaces the above
    def _registered_reactions_hook(self):
        event_types = super()._registered_reactions_hook()
        if self.tabindex is None:
            for event_type in event_types:
                if event_type in ('key_down', 'key_up', 'key_press'):
                    self.set_tabindex(-1)
        return event_types
    
    def _init_events(self):
        # Connect some standard events
        self._addEventListener(self.node, 'mousedown', self.mouse_down, 0)
        self._addEventListener(self.node, 'wheel', self.mouse_wheel, 0)
        self._addEventListener(self.node, 'keydown', self.key_down, 0)
        self._addEventListener(self.node, 'keyup', self.key_up, 0)
        self._addEventListener(self.node, 'keypress', self.key_press, 0)
        
        # Implement mouse capturing. When a mouse is pressed down on
        # a widget, it "captures" the mouse, and will continue to receive
        # move and up events, even if the mouse is not over the widget.

        self._capture_flag = None

        def capture(e):
            # On FF, capture so we get events when outside browser viewport
            if self.CAPTURE_MOUSE and self.node.setCapture:
                self.node.setCapture()
            self._capture_flag = 2
            window.document.addEventListener("mousemove", mouse_outside, True)
            window.document.addEventListener("mouseup", mouse_outside, True)

        def release():
            self._capture_flag = 1
            window.document.removeEventListener("mousemove", mouse_outside, True)
            window.document.removeEventListener("mouseup", mouse_outside, True)

        def mouse_inside(e):
            if self._capture_flag == 1:
                self._capture_flag = 0
            elif not self._capture_flag:
                if e.type == 'mousemove':
                    self.mouse_move(e)
                elif e.type == 'mouseup':
                    self.mouse_up(e)

        def mouse_outside(e):
            if self._capture_flag:  # Should actually always be 0
                e = window.event if window.event else e
                if e.type == 'mousemove':
                    self.mouse_move(e)
                elif e.type == 'mouseup':
                    release()
                    self.mouse_up(e)
        
        # todo: only start capturing move events when mouse is down, unless some flag is set
        # Setup capturing and releasing
        self._addEventListener(self.node, 'mousedown', capture, True)
        self._addEventListener(self.node, "losecapture", release)
        # Subscribe to normal mouse events
        self._addEventListener(self.node, "mousemove", mouse_inside, False)
        self._addEventListener(self.node, "mouseup", mouse_inside, False)

    @event.emitter
    def mouse_down(self, e):
        """ Event emitted when the mouse is pressed down.

        A mouse event has the following attributes:

        * pos: the mouse position, in pixels, relative to this widget
        * page_pos: the mouse position relative to the page
        * button: what button the event is about, 1, 2, 3 are left, right,
            middle, respectively. 0 indicates no button.
        * buttons: what buttons where pressed at the time of the event.
        * modifiers: list of strings "Alt", "Shift", "Ctrl", "Meta" for
            modifier keys pressed down at the time of the event.
        """
        return self._create_mouse_event(e)

    @event.emitter
    def mouse_up(self, e):
        """ Event emitted when the mouse is pressed up.

        See mouse_down() for a description of the event object.
        """
        ev = self._create_mouse_event(e)
        return ev

    @event.emitter
    def mouse_move(self, e):
        """ Event fired when the mouse is moved inside the canvas.
        See mouse_down for details.
        """

        ev = self._create_mouse_event(e)
        ev.button = 0
        return ev

    @event.emitter
    def mouse_wheel(self, e):
        """ Event emitted when the mouse wheel is used.

        See mouse_down() for a description of the event object.
        Additional event attributes:

        * hscroll: amount of scrolling in horizontal direction
        * vscroll: amount of scrolling in vertical direction
        """
        # Note: wheel event gets generated also for parent widgets
        # I think this makes sense, but there might be cases
        # where we want to prevent propagation.
        ev = self._create_mouse_event(e)
        ev.button = 0
        ev.hscroll = e.deltaX * [1, 16, 600][e.deltaMode]
        ev.vscroll = e.deltaY * [1, 16, 600][e.deltaMode]
        return ev

    def _create_mouse_event(self, e):
        # note: our button has a value as in JS "which"
        modifiers = [n for n in ('Alt', 'Shift', 'Ctrl', 'Meta')
                        if e[n.lower()+'Key']]
        # Fix position
        pos = e.clientX, e.clientY
        rect = self.node.getBoundingClientRect()
        offset = rect.left, rect.top
        pos = float(pos[0] - offset[0]), float(pos[1] - offset[1])
        # Fix buttons
        if e.buttons:
            buttons_mask = reversed([c for c in e.buttons.toString(2)]).join('')
        else:
            # libjavascriptcoregtk-3.0-0  version 2.4.11-1 does not define
            # e.buttons
            buttons_mask = [e.button.toString(2)]
        buttons = [i+1 for i in range(5) if buttons_mask[i] == '1']
        button = {0: 1, 1: 3, 2: 2, 3: 4, 4: 5}[e.button]
        # Create event dict
        return dict(pos=pos, page_pos=(e.pageX, e.pageY),
                    button=button, buttons=buttons,
                    modifiers=modifiers,
                    )

    @event.emitter
    def key_down(self, e):
        """ Event emitted when a key is pressed down while this
        widget has focus. A key event has the following attributes:

        * key: the character corresponding to the key being pressed, or
            a key name like "Escape", "Alt", "Enter".
        * modifiers: list of strings "Alt", "Shift", "Ctrl", "Meta" for
            modifier keys pressed down at the time of the event.
        
        A browser may associate certain actions with certain key presses.
        If this browser action is unwanted, it can be disabled by
        overloading this emitter:
        
        .. code-block:: py
        
            @event.emitter
            def key_down(self, e):
                # Prevent browser's default reaction to function keys
                ev = super().key_press(e)
                if ev.key.startswith('F'):
                    e.preventDefault()
                return ev
        """
        return self._create_key_event(e)
    
    @event.emitter
    def key_up(self, e):
        """ Event emitted when a key is released while
        this widget has focus. See key_down for details.
        """
        return self._create_key_event(e)

    @event.emitter
    def key_press(self, e):
        """ Event emitted when a key is pressed down. This event does not
        fire for the pressing of a modifier keys. See key_down for details.
        """
        return self._create_key_event(e)

    def _create_key_event(self, e):
        # https://developer.mozilla.org/en-US/docs/Web/API/KeyboardEvent
        # key: chrome 51, ff 23, ie 9
        # code: chrome ok, ff 32, ie no
        modifiers = [n for n in ('Alt', 'Shift', 'Ctrl', 'Meta')
                        if e[n.lower()+'Key']]
        key = e.key
        if not key and e.code:  # Chrome < v51
            key = e.code
            if key.startswith('Key'):
                key = key[3:]
                if 'Shift' not in modifiers:
                    key = key.lower()
            elif key.startswith('Digit'):
                key = key[5:]
        # todo: handle Safari and older browsers via keyCode
        key = {'Esc': 'Escape', 'Del': 'Delete'}.get(key, key)  # IE
        return dict(key=key, modifiers=modifiers)
