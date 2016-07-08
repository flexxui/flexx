"""
.. UIExample:: 100

    from flexx import app, ui

    class Example(ui.Widget):
        ''' A red widget '''
        CSS = ".flx-Example {background:#f00; min-width:20px; min-height:20px;}"

"""

from .. import event
from ..app import Model, call_later, get_active_model
from ..pyscript import undefined, window


class LiveKeeper:
    """ This little utility keeps objects alive for a set period of
    time. This is used to prevent Widget objects from being cleaned up
    by the garbadge collector when they are only referenced by the
    "children" property of their parent. Due to synchronization, the
    children property can "jitter", causing references of objects to
    be lost.
    """

    def __init__(self):
        self._objects = {}

    def keep(self, ob, timeout=5.0):
        i = id(ob)
        self._objects[i] = ob
        call_later(timeout, self.clear, i)

    def clear(self, i):
        self._objects.pop(i, None)

liveKeeper = LiveKeeper()


# To give both JS and Py a parent property without having it synced,
# it is set explicitly for both sides. We need to sync either parent
# or children to communicate the parenting structure, otherwise we end
# up in endless loops. We use the children for this, because it contains
# ordering information which cannot be communicated by the parent prop
# alone.

def parent(self, new_parent=None):
    """ The parent widget, or None if it has no parent. Setting
    this property will update the "children" property of the
    old and new parent.
    """
    old_parent = self.parent  # or None

    if new_parent is old_parent:
        return new_parent
    if not (new_parent is None or isinstance(new_parent, Widget)):
        raise ValueError('parent must be a Widget or None')

    if old_parent is not None:
        children = list(old_parent.children if old_parent.children else [])
        while self in children:
            children.remove(self)
        old_parent.children = children
    if new_parent is not None:
        children = list(new_parent.children if new_parent.children else [])
        children.append(self)
        new_parent.children = children

    return new_parent



class Widget(Model):
    """ Base widget class.

    When *subclassing* a Widget to create a compound widget (a widget
    that acts as a container for other widgets), use the ``init()``
    method to initialize the child widgets. This method is called while
    the widget is the current widget. Similarly, the ``init()`` method
    of the JS part of a subclass can be used to initialize the Widget
    (e.g. create the Phosphor widget and HTML DOM elements).

    """

    CSS = """

    .flx-container {
        min-height: 10px; /* splitter sets its own minsize if contained */
    }

    .flx-Widget {
        box-sizing: border-box;
        white-space: nowrap;
        overflow: hidden;
    }

    .flx-main-widget {
       width: 100%;
       height: 100%;
    }

    """

    def __init__(self, **kwargs):

        # Handle parent
        parent = kwargs.pop('parent', None)
        if parent is None:
            active_model = get_active_model()
            if isinstance(active_model, Widget):
                parent = active_model
        kwargs['parent'] = parent

        # Use parent session unless session was given
        if parent is not None and not kwargs.get('session', None):
            kwargs['session'] = parent.session

        # Set container if this widget represents the main app
        if kwargs.get('is_app', False):
            kwargs['container'] = 'body'

        # Init - pass signal values via kwargs
        Model.__init__(self, **kwargs)
        
        # All widgets need phosphor
        self._session.use_global_asset('phosphor-all.js', before='flexx-ui.css')

    def _repr_html_(self):
        """ This is to get the widget shown inline in the notebook.
        """
        if self.container:
            return "<i>This widget is already shown in this notebook</i>"

        container_id = self.id + '_container'
        self._set_prop('container', container_id)
        return "<div class='flx-container' id=%s />" % container_id

    def init(self):
        """ Overload this to initialize a cusom widget. When called, this
        widget is the current parent.
        """
        pass

    def dispose(self):
        """ Overloaded version of dispose() that will also
        dispose any child widgets.
        """
        children = self.children
        super().dispose()
        for child in children:
            child.dispose()

    @event.connect('parent:aaa')
    def __keep_alive(self, *events):
        # When the parent changes, we prevent the widget from being deleted
        # for a few seconds, to it will survive parent-children "jitter".
        liveKeeper.keep(self)
    
    parent = event.prop(parent)
    
    class Both:
        
        @event.prop
        def title(self, v=''):
            """ The title of this widget. This is used to mark the widget
            in e.g. a tab layout or form layout.
            """
            return str(v)
    
        @event.prop
        def style(self, v=''):
            """ CSS style options for this widget object. e.g.
            ``"background: #f00; color: #0f0;"``. If the given value is a
            dict, its key-value pairs are converted to a CSS style string.
            Note that the CSS class attribute can be used to style all
            instances of a class.
            """
            if isinstance(v, dict):
                v = ['%s: %s' % (k, v) for k, v in v.items()]
                v = '; '.join(v)
            return str(v)
    
        @event.prop
        def flex(self, v=0):
            """ How much space this widget takes (relative to the other
            widgets) when contained in a flexible layout such as BoxLayout,
            BoxPanel, FormLayout or GridPanel. A flex of 0 means to take
            the minimum size. Flex is a two-element tuple, but both values
            can be specified at once by specifying a scalar.
            """
            if isinstance(v, (int, float)):
                v = v, v
            return float(v[0]), float(v[1])
    
        @event.prop
        def pos(self, v=(0, 0)):
            """ The position of the widget when it in a layout that allows
            positioning, this can be an arbitrary position (e.g. in
            PinBoardLayout) or the selection of column and row in a
            GridPanel.
            """
            return float(v[0]), float(v[1])
    
        @event.prop
        def base_size(self, v=(0, 0)):
            """ The given size of the widget when it is in a layout that
            allows explicit sizing, or the base-size in a BoxPanel or
            GridPanel. A value <= 0 is interpreted as auto-size.
            """
            return float(v[0]), float(v[1])
    
        @event.prop
        def tabindex(self, v=-1):
            """ The index used to determine widget order when the user
            iterates through the widgets using tab.
            """
            return int(v)
    
        # Also see size readonly defined in JS
    
        @event.prop
        def container(self, v=''):
            """ The id of the DOM element that contains this widget if
            parent is None. Use 'body' to make this widget the root.
            """
            return str(v)
    
        @event.prop
        def children(self, new_children=()):
            """ The child widgets of this widget. Setting this property
            will update the "parent" property of the old and new
            children.
            """
            old_children = self.children
            if not old_children:  # Can be None during initialization
                old_children = []
    
            if len(new_children) == len(old_children):
                if all([(c1 is c2) for c1, c2 in zip(old_children, new_children)]):
                    return new_children  # No need to do anything
            if not all([isinstance(w, Widget) for w in new_children]):
                raise ValueError('All children must be widget objects.')
    
            for child in old_children:
                if child not in new_children:
                    child.parent = None
            for child in new_children:
                if child not in old_children:
                    child.parent = self
            return tuple(new_children)

    class JS:
        
        parent = event.prop(parent)
        
        def __init__(self, *args):
            super().__init__(*args)

            # Let widget create Phoshor and DOM nodes
            self._init_phosphor_and_node()
            # Set outernode. Usually, but not always equal to self.node
            self.outernode = self.phosphor.node

            # Setup JS events to enter Flexx' event system
            self._init_events()

            # Keep track of size
            that = self
            class SizeNotifier:
                def filterMessage(handler, msg):
                    if msg._type == 'resize':
                        that._check_real_size()
                    return False
            window.phosphor.messaging.installMessageFilter(self.phosphor,
                                                           SizeNotifier())

            # Derive css class name
            cls_name = self._class_name
            for i in range(32):  # i.e. a safe while-loop
                self.outernode.classList.add('flx-' + cls_name)
                cls = window.flexx.classes[cls_name]
                if not cls:
                    break
                cls_name = cls.prototype._base_class._class_name
                if not cls_name or cls_name == 'Model':
                    break
            else:
                raise RuntimeError('Error while determining class names')

        def _init_phosphor_and_node(self):
            """ Overload this in sub widgets.
            """
            self.phosphor = window.phosphor.panel.Panel()
            self.node = self.phosphor.node

        @event.connect('style')
        def __style_changed(self, *events):
            """ Emits when the style signal changes, and provides a dict with
            the changed style atributes.
            """
            # self.node.style = style  # forbidden in strict mode,
            # plus it clears all previously set style

            # Note that styling is applied to the outer node, just like
            # the styling defined via the CSS attribute. In most cases
            # the inner and outer node are the same, but not always
            # (e.g. CanvasWidget).

            # Set style elements, keep track in a dict
            d = {}
            for ev in events:
                style = ev.new_value
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
                # Clear phosphor's limit cache (no need for getComputedStyle())
                values = [self.outernode.style[k] for k in size_limits_keys]
                # todo: do I need a variant of self.phosphor.clearSizeLimits()?
                for k, v in zip(size_limits_keys, values):
                    self.outernode.style[k] = v
                # Allow parent to re-layout
                parent = self.parent
                if parent:
                    parent.phosphor.fit()  # i.e. p.processMessage(p.MsgFitRequest)
                self.phosphor.update()

        @event.connect('title')
        def __title_changed(self, *events):
            # All Phosphor widgets have a title
            self.phosphor.title.text = events[-1].new_value

        ## Size

        @event.readonly
        def size(self, v=(0, 0)):
            """ The actual size of the widget. Flexx tries to
            keep this value up-to-date, but when in a layout like
            BoxLayout, a change in a Button's text can change the size
            of sibling widgets.
            """
            return v[0], v[1]

        @event.connect('container', 'parent.size', 'children')
        def check_size(self, *events):
            """ Check the current size of this widget. It is normally
            not necessary to call this method directly, but there are (rare)
            cases when Flexx is otherwise unaware of a change in size.
            """
            # Check size in *next* event loop iter to give the DOM a
            # chance to settle.
            window.setTimeout(self._check_real_size, 0)

        def _check_real_size(self, notify_parent=False):
            """ Check whether the current size has changed.
            """
            n = self.outernode
            cursize = self.size
            if cursize[0] != n.clientWidth or cursize[1] != n.clientHeight:
                self._set_prop('size', [n.clientWidth, n.clientHeight])
                # Notify parent? This is basically a hook box layout
                if notify_parent and self.parent:
                    if self.parent.let_children_check_size:
                        self.parent.let_children_check_size()

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

        @event.connect('container')
        def __container_changed(self, *events):
            id = events[-1].new_value
            self.outernode.classList.remove('flx-main-widget')
            if self.parent:
                return
            # Detach
            if self.phosphor.isAttached:
                self.phosphor.detach()
            if self.outernode.parentNode is not None:  # detachWidget not enough
                self.outernode.parentNode.removeChild(self.outernode)
            # Attach
            if id:
                if id == 'body':
                    el = window.document.body
                else:
                    el = window.document.getElementById(id)
                self.phosphor.attach(el)
                window.addEventListener('resize', lambda: (self.phosphor.update(),
                                                           self._check_real_size()))
            if id == 'body':
                self.outernode.classList.add('flx-main-widget')
            elif id:
                # Update style. If there is stuff like min-height set (which
                # would be common in the notebook), we need to reapply style
                # because Phosphor sets some of the size-styling too.
                style = self.style
                window.setTimeout(lambda: (self._set_prop('style', ''),
                                           self._set_prop('style', style)), 1)

        @event.connect('children')
        def __children_changed(self, *events):
            """ Hook to make child widgets appear in the right order in a
            layout. Widget provides a default implementation. Layouts should
            overload _add_child() and _remove_child().
            """
            new_children = events[-1].new_value
            old_children = events[0].old_value

            i_ok = 0
            for i in range(min(len(new_children), len(old_children))):
                if new_children[i] is not old_children[i]:
                    break
                i_ok = i

            for child in old_children[i_ok:]:
                self._remove_child(child)
            for child in new_children[i_ok:]:
                self._add_child(child)

        def _add_child(self, widget):
            """ Add the DOM element. Called right after the child widget
            is added. Overloadable by layouts.
            """
            self.phosphor.addChild(widget.phosphor)

        def _remove_child(self, widget):
            """ Remove the DOM element. Called right after the child
            widget is removed. Overloadable by layouts.
            """
            widget.phosphor.parent = None

        ## Events

        # todo: events: focus, enter, leave ... ?

        CAPTURE_MOUSE = False

        def _init_events(self):
            # Connect some standard events
            self.node.addEventListener('mousedown', self.mouse_down, 0)
            self.node.addEventListener('wheel', self.mouse_wheel, 0)
            self.node.addEventListener('keydown', self.key_down, 0)
            self.node.addEventListener('keyup', self.key_up, 0)
            self.node.addEventListener('keypress', self.key_press, 0)

            # Disable context menu so we can handle RMB clicks
            _context_menu = lambda ev: ev.preventDefault() and False
            self.node.addEventListener('contextmenu', _context_menu, 0)

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

            # Setup capturing and releasing
            self.node.addEventListener('mousedown', capture, True)
            self.node.addEventListener("losecapture", release)
            # Subscribe to normal mouse events
            self.node.addEventListener("mousemove", mouse_inside, False)
            self.node.addEventListener("mouseup", mouse_inside, False)

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
            """ Event emitted when a key is pressed down. This event
            does not fire for the pressing of a modifier keys. See
            key_down for details.
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

        ## Special

        @event.connect('tabindex')
        def __update_tabindex(self, *events):
            # Note that this also makes the widget able to get focus, and this
            # able to do key events.
            self.node.tabIndex = events[-1].new_value
        
        @event.connect('children')
        def __make_singleton_container_widgets_work(self, *events):
            # This fixes an issue related to a vbox in a widget in a
            # vbox on Chrome. If this is a plain widget, and it has one
            # child that is a HBox or VBox, we need to act like a flex
            # container.
            # Note that we should *not* set the display style attribute
            # directly, as that would break down in situations where
            # the widget must be hidden, such as in a tab panel.
            if 'flx-Layout' not in self.outernode.className:
                self.outernode.classList.remove('flx-hbox')
                self.outernode.classList.remove('flx-vbox')
                children = self.children
                if len(children) == 1:
                    subClassName = children[0].outernode.className
                    if 'flx-VBox' in subClassName:
                        self.outernode.classList.add('flx-hbox')
                    elif 'flx-HBox' in subClassName:
                        self.outernode.classList.add('flx-vbox')
