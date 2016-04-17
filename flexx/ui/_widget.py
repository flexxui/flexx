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
from ..pyscript import undefined, window

def _check_two_scalars(name, v):
    if not (isinstance(v, (list, tuple)) and
            isinstance(v[0], (int, float)) and
            isinstance(v[1], (int, float))):
        raise ValueError('%s must be a tuple of two scalars.' % name)
    return float(v[0]), float(v[1])


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


# todo: the Python version of widgets are not stored now, causing cleanup
# at the wrong moment. Even when orphaned, the object may have a reference
# at the JS side, and could be added to the tree later. -> cleanup when
# disposed, not earlier.
# Maybe we just need to make sure that paren-children are stored in Python,
# if you orphan a widget and did not keep a ref. Maybe thats intended, and the
# ref should be deleted in JS too...


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
        def set_cointainer_id():
            self._set_prop('container', container_id)
        # Set container id, this gets applied in the next event loop
        # iteration, so by the time it gets called in JS, the div that
        # we define below will have been created.
        from ..app import call_later
        call_later(0.1, set_cointainer_id)  # todo: always do calls in next iter
        # todo: no need for call_later anymore, since events are always later!
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
            v = '; '.join('%s: s%' % (k, v) for k, v in v.items())
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
        return _check_two_scalars('flex', v)
    
    @event.prop
    def pos(self, v=(0, 0)):
        """ The position of the widget when it in a layout that allows
        positioning, this can be an arbitrary position (e.g. in
        PinBoardLayout) or the selection of column and row in a
        GridPanel.
        """
        return _check_two_scalars('pos', v)
    
    @event.prop
    def base_size(self, v=(0, 0)):
        """ The given size of the widget when it is in a layout that
        allows explicit sizing, or the base-size in a BoxPanel or
        GridPanel. A value <= 0 is interpreted as auto-size.
        """
        return _check_two_scalars('base_size', v)
    
    # Also see size readonly defined in JS
    
    @event.prop
    def container(self, v=''):
        """ The id of the DOM element that contains this widget if
        parent is None. Use 'body' to make this widget the root.
        """
        return str(v)
    
    
    class JS:
        
        def __init__(self, *args):
            super().__init__(*args)
            
            # Get phosphor widget that is set in init()
            if not self.p:
                self.p = window.phosphor.panel.Panel()
            self.node = self.p.node
            
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
        
        @event.prop
        def parent(self, new_parent=None):
            """ The parent widget, or None if it has no parent. Setting
            this property will update the "children" property of the
            old and new parent.
            """
            old_parent = self.parent or None
            
            if new_parent is old_parent:
                return new_parent
            if not (new_parent is None or isinstance(new_parent, flexx.classes.Widget)):
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
        
        @event.prop
        def children(self, new_children=()):
            """ The child widgets of this widget. Setting this property
            will update the "parent" property of the old and new
            children.
            """
            old_children = self.children if self.children else []
            
            if len(new_children) == len(old_children):
                if all([(c1 is c2) for c1, c2 in zip(old_children, new_children)]):
                    return new_children  # No need to do anything
            if not all([isinstance(w, flexx.classes.Widget) for w in new_children]):
                raise ValueError('All children must be widget objects.')
            
            for child in old_children:
                if child not in new_children:
                    child.parent = None
            for child in new_children:
                if child not in old_children:
                    child.parent = self
            
            return tuple(new_children)
        
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
        
        ## Special
        
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
