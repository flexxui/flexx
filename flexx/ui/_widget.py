"""
.. UIExample:: 100
    
    from flexx import app, ui
    
    class Example(ui.Widget):
        ''' A red widget '''
        CSS = ".flx-Example {background:#f00; min-width:20px; min-height:20px;}"

"""

import threading

from .. import event
from ..app import Model
from ..pyscript import undefined, window, this_is_js


# Keep track of stack of default parents when using widgets
# as context managers. Have one list for each thread.

_default_parents_per_thread = {}  # dict of threadid -> list

def _get_default_parents():
    """ Get list that represents the stack of default parents.
    Each thread has its own stack.
    """
    # Get thread id
    if hasattr(threading, 'current_thread'):
        tid = id(threading.current_thread())
    else:
        tid = id(threading.currentThread())
    # Get list of parents for this thread
    return _default_parents_per_thread.setdefault(tid, [])



class Widget(Model):
    """ Base widget class.
    
    When *subclassing* a Widget to create a compound widget (a widget
    that serves as a container for other widgets), use the ``init()``
    method to initialize child widgets. This method is called while
    the widget is the current widget.
    
    When subclassing to create a custom widget use the ``_init()``
    method both for the Python and JS version of the class.
    
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
        
        # Apply default parent?
        parent = kwargs.pop('parent', None)
        if parent is None:
            default_parents = _get_default_parents()
            if default_parents:
                parent = default_parents[-1]
        kwargs['parent'] = parent
        
        # Use parent session unless session was given
        if parent is not None and not kwargs.get('session', None):
            kwargs['session'] = parent.session
        
        # Set container if this widget represents the main app
        if kwargs.get('is_app', False):
            kwargs['container'] = 'body'
        
        # Need to prepare parent and children because they are mutually dependent
        self._parent_value = None
        self._children_value = ()
        
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
        
        # todo: no need for call_later anymore, right?
        # def set_cointainer_id():
        #     self._set_prop('container', container_id)
        # # Set container id, this gets applied in the next event loop
        # # iteration, so by the time it gets called in JS, the div that
        # # we define below will have been created.
        # from ..app import call_later
        # call_later(0.1, set_cointainer_id)  # todo: always do calls in next iter
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
    
    def __enter__(self):
        # Note that __exit__ is guaranteed to be called, so there is
        # no need to use weak refs for items stored in default_parents
        default_parents = _get_default_parents()
        default_parents.append(self)
        return self
    
    def __exit__(self, type, value, traceback):
        default_parents = _get_default_parents()
        assert self is default_parents.pop(-1)
    
    @event.prop(both=True)
    def title(self, v=''):
        """ The title of this widget. This is used to mark the widget
        in e.g. a tab layout or form layout.
        """
        return str(v)
    
    @event.prop(both=True)
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
    
    @event.prop(both=True)
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
    
    @event.prop(both=True)
    def pos(self, v=(0, 0)):
        """ The position of the widget when it in a layout that allows
        positioning, this can be an arbitrary position (e.g. in
        PinBoardLayout) or the selection of column and row in a
        GridPanel.
        """
        return float(v[0]), float(v[1])
    
    @event.prop(both=True)
    def base_size(self, v=(0, 0)):
        """ The given size of the widget when it is in a layout that
        allows explicit sizing, or the base-size in a BoxPanel or
        GridPanel. A value <= 0 is interpreted as auto-size.
        """
        return float(v[0]), float(v[1])
    
    @event.prop(both=True)
    def tabindex(self, v=-1):
        """ The index used to determine widget order when the user
        iterates through the widgets using tab.
        """
        return int(v)
    
    # Also see size readonly defined in JS
    
    @event.prop(both=True)
    def container(self, v=''):
        """ The id of the DOM element that contains this widget if
        parent is None. Use 'body' to make this widget the root.
        """
        return str(v)
    
    # The parent is not synced; we need to sync either parent or children
    # to communicate the parenting structure, otherwise we end up in endless
    # loops. We use the children for this, because it contains ordering
    # information which cannot be communicated by the parent prop alone.
    
    @event.prop(both=True, sync=False)
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
    
    @event.prop(both=True)
    def children(self, new_children=()):
        """ The child widgets of this widget. Setting this property
        will update the "parent" property of the old and new
        children.
        """
        old_children = self.children# if self.children else []
        
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
        
        def __init__(self, *args):
            # Need to prepare parent and children because they are mutually dependent
            self._parent_value = None
            self._children_value = []
            super().__init__(*args)
            
            # Get phosphor widget that is set in init()
            if not self.p:
                self.p = window.phosphor.panel.Panel()
            self.node = self.p.node
            
            # Connect same standard events
            self.node.addEventListener('mousedown', self.mouse_down, 0)
            self.node.addEventListener('mouseup', self.mouse_up, 0)
            self.node.addEventListener('keydown', self.key_down, 0)
            self.node.addEventListener('keyup', self.key_up, 0)
            self.node.addEventListener('keypress', self.key_press, 0)
            
            # Keep track of size
            that = self
            class SizeNotifier:
                def filterMessage(handler, msg):
                    if msg._type == 'resize':
                        that._check_real_size()
                    return False
            window.phosphor.messaging.installMessageFilter(self.p, SizeNotifier())
            
            # Derive css class name
            cls_name = self._class_name
            for i in range(32):  # i.e. a safe while-loop
                self.node.classList.add('flx-' + cls_name)
                cls = window.flexx.classes[cls_name]
                if not cls:
                    break
                cls_name = cls.prototype._base_class._class_name
                if not cls_name or cls_name == 'Model':
                    break
            else:
                raise RuntimeError('Error while determining class names')
        
        @event.connect('style')
        def __style_changed(self, *events):
            """ Emits when the style signal changes, and provides a dict with
            the changed style atributes.
            """
            # self.node.style = style  # forbidden in strict mode,
            # plus it clears all previously set style
            
            # Set style elements, keep track in a dict
            d = {}
            for ev in events:
                style = ev.new_value
                if style:
                    for part in style.split(';'):
                        if ':' in part:
                            key, val = part.split(':')
                            key, val = key.trim(), val.trim()
                            self.node.style[key] = val
                            d[key] = val
            
            # Did we change style related to sizing?
            size_limits_keys = 'min-width', 'min-height', 'max-width', 'max-height'
            size_limits_changed = False
            for key in size_limits_keys:
                if key in d:
                    size_limits_changed = True
            
            if size_limits_changed:
                # Clear phosphor's limit cache (no need for getComputedStyle())
                values = [self.node.style[k] for k in size_limits_keys]
                # todo: do I need a variant of self.p.clearSizeLimits()?
                for k, v in zip(size_limits_keys, values):
                    self.node.style[k] = v
                # Allow parent to re-layout
                parent = self.parent
                if parent:
                    parent.p.fit()  # i.e. p.processMessage(p.MsgFitRequest)

        @event.connect('title')
        def __title_changed(self, *events):
            # All Phosphor widgets have a title
            self.p.title.text = events[-1].new_value
        
        ## Size 
        
        @event.readonly
        def size(self, v=(0, 0)):
            """ The actual size of the widget. Flexx tries to
            keep this value up-to-date, but when in a layout like
            BoxLayout, a change in a Button's text can change the size
            of sibling widgets.
            """
            return v[0], v[1]
        
        @event.connect('container', 'parent', 'children')
        def __update_size(self, *events):
            # Check size in *next* event loop iter to give the DOM a
            # chance to settle
            window.setTimeout(self._check_real_size, 0)
        
        def _check_real_size(self):
            """ Check whether the current size has changed.
            """
            n = self.node
            cursize = self.size
            if cursize[0] != n.clientWidth or cursize[1] !=n.clientHeight:
                self._set_prop('size', [n.clientWidth, n.clientHeight])
        
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
            self.node.style[prefix + 'width'] = size[0]
            self.node.style[prefix + 'height'] = size[1]
        
        ## Parenting
        
        @event.connect('container')
        def __container_changed(self, *events):
            id = events[-1].new_value
            self.node.classList.remove('flx-main-widget')
            if self.parent:
                return 
            if id:
                el = window.document.getElementById(id)
                if self.p.isAttached:
                    self.p.detach()
                if self.node.parentNode is not None:  # detachWidget not enough
                    self.node.parentNode.removeChild(self.node)
                self.p.attach(el)
                window.addEventListener('resize', lambda: (self.p.update(), 
                                                           self._check_real_size()))
            if id == 'body':
                self.node.classList.add('flx-main-widget')
        
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
            """ Add the DOM element.
            Called right after the child widget is added. """
            self.p.addChild(widget.p)
        
        def _remove_child(self, widget):
            """ Remove the DOM element.
            Called right after the child widget is removed.
            """
            widget.p.parent = None
        
        ## Events
        
        # todo: events: mouse_move?,focus, enter, leave ...
        
        @event.emitter
        def mouse_down(self, e):
            """ Event emitted when the mouse is pressed down.
            
            A mouse event has the following attributes:
            * x: the x location, in pixels, relative to this widget
            * y: the y location, in pixels, relative to this widget
            * pageX: the x location relative to the page
            * pageY: the y location relative to the page
            * button: what button the event is about, 1, 2, 3 are left, middle,
              right, respectively.
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
            return self._create_mouse_event(e)
        
        def _create_mouse_event(self, e):
            # note: our button has a value as in JS "which"
            modifiers = [n for n in ('Alt', 'Shift', 'Ctrl', 'Meta')
                         if e[n.lower()+'Key']]
            pos = e.clientX, e.clientY
            rect = self.node.getBoundingClientRect()
            offset = rect.left, rect.top
            x, y = float(pos[0] - offset[0]), float(pos[1] - offset[1])
            return dict(x=x, y=y, pageX=e.pageX, pageY=e.pageY,
                        button=e.button+1, buttons=[b+1 for b in e.buttons],
                        modifiers=modifiers,
                        )
        
        @event.emitter
        def key_down(self, e):
            """ Event emitted when a key is pressed down while
            this widget has focus..
            
            A key event has the following attributes:
            * key: the character corresponding to the key being pressed, or
              a key name like "Escape", "Alt", "Enter" otherwise.
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
            """Event emitted when a key is pressed down. This event
            does not handle the pressing of modifier keys. See key_down
            for details.
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
        def __update_css(self, *events):
            children = events[-1].new_value
            if 'flx-Layout' not in self.node.className:
                # Ok, no layout, so maybe we need to take care of CSS.
                # If we have a child that is a hbox/vbox, we need to be a
                # flex container.
                self.node.style['display'] = ''
                self.node.style['flex-flow'] = ''
                if len(children) == 1:
                    subClassName = children[0].node.className
                    if 'flx-hbox' in subClassName:
                        self.node.style['display'] = 'flex'
                        self.node.style['flex-flow'] = 'row'
                    elif 'flx-vbox' in subClassName:
                        self.node.style['display'] = 'flex'
                        self.node.style['flex-flow'] = 'column'

 
    