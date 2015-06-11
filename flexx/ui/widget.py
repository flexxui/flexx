""" The base widget class.

Implements parenting and other things common to all widgets.
"""

import json
import threading

from ..pyscript import js
from ..properties import Prop, Instance, Str, Tuple, Float, FloatPair
from . import Mirrored, get_instance_by_id


class WidgetProp(Prop):
    _default = None
    
    def validate(self, val):
        if val is None or isinstance(val, Widget):
            return val
        else:
            raise ValueError('Prop %r must be a Widget or None, got %r' % 
                             (self.name, val.__class__.__name__))
    
    def to_json(self, value):
        # Widgets are kept track of via their id
        if value is None:
            return json.dumps(None)
        return json.dumps(value.id)
    
    def from_json(self, txt):
        return get_instance_by_id(json.loads(txt))
    
    @js
    def to_json__js(self, value):
        if value is None:
            return JSON.stringify(None)
        else:
            return JSON.stringify(value.id)
    
    @js
    def from_json__js(self, value):
        return flexx.instances[JSON.parse(value)]


# todo: would be nice if Tuple just worked with elements that need custom json ...
class WidgetsProp(Tuple):
    
    def __init__(self, *args, **kwargs):
        Tuple.__init__(self, WidgetProp, *args, **kwargs)
    
    @js
    def to_json__js(self, value):
        res = '  '
        for v in value:
            if v is None or v.id is undefined:
                res += JSON.stringify(None)
            else:
                res += JSON.stringify(v.id)
            res += ', '
        return '[' + res[:-2] + ']'
    
    @js
    def from_json__js(self, value):
        res = []
        for v in JSON.parse(value):
            res.append(flexx.instances[v])
        return res


# Keep track of stack of default parents when using widgets
# as context managers. Have one list for each thread.

_default_parents_per_thread = {}  # dict of threadid -> list

def _get_default_parents():
    """ Get list that represents the stack of default parents.
    Each thread has its own stack.
    """
    # Get thread id
    if hasattr(threading, 'current_thread'):
        id = threading.current_thread().ident
    else:
        id = threading.currentThread().ident
    # Get list of parents for this thread
    return _default_parents_per_thread.setdefault(id, [])


class Widget(Mirrored):
    """ Base widget class.
    
    In HTML-speak, this represents a plain div-element. Not very useful
    on itself, except perhaps for spacing. Subclass to create something
    interesting.
    
    Example:
    
    .. UIExample:: 100
    
        from flexx import ui
        
        class MyWidget(ui.Widget):
            CSS = ".flx-mywidget {background:#f00;}"
        
        class App(ui.App):
            def init(self):
                with ui.HBox():  # show our widget full-window
                    MyWidget(flex=1)
    
    """
    
    CSS = """
    
    .flx-widget {
        box-sizing: border-box;
        white-space: nowrap;
        overflow: hidden;
    }
    """
    
    _EVENT_NAMES = ['resize']
    
    # Properties
    
    container_id = Str()  # used if parent is None
    
    parent = WidgetProp(help="The parent widget")
    flex = Float(help="How much space this widget takes when contained in a " + 
                      "layout. A flex of 0 means to take the minimum size.")
    pos = FloatPair()
    size = FloatPair()
    
    min_width = Float()
    min_height = Float()  # todo: or min_size?
    cssClassName = Str()  # todo: should this be private? Or can we calculate it in JS?
    
    def __init__(self, parent=None, **kwargs):
        # todo: -> parent is widget or ref to div element
        
        # Childen are not exposed via a HasProps Property, because its
        # sort of a side-effect of the parent property.
        self._children = ()
        
        # Apply default parent?
        if parent is None:
            default_parents = _get_default_parents()
            if default_parents:
                parent = default_parents[-1]
        
        # Provide css class name to 
        classes = ['flx-' + c.__name__.lower() for c in self.__class__.mro()]
        classname = ' '.join(classes[:1-len(Widget.mro())])
        
        # Pass properties via kwargs
        kwargs['cssClassName'] = classname
        kwargs['parent'] = parent
        Mirrored.__init__(self, **kwargs)
    
    # @js
    # def _js__init__(self):
    #     self.children = []  # Init children property
    #     super().__init__(*arguments)
    
    def __enter__(self):
        # Note that __exit__ is guaranteed to be called, so there is
        # no need to use weak refs for items stored in default_parents
        default_parents = _get_default_parents()
        default_parents.append(self)
        return self
    
    def __exit__(self, type, value, traceback):
        default_parents = _get_default_parents()
        assert self is default_parents.pop(-1)
        #if value is None:
        #    self.update()
    
    @js
    def _js_init(self):
        """ We use _init() instead of __init__; at this point the prop
        values are initialized, and the prop changed functions are
        called *after* this.
        """
        self.children = []
        self._create_node()
        flexx.get('body').appendChild(this.node)
        # todo: allow setting a placeholder DOM element, or any widget parent
        
        # Create closure to check for size changes
        self._stored_size = 0, 0
        that = this
        def _check_resize():
            # Re-raise in next event loop iteration
            setTimeout(_check_resize_now, 0)
        def _check_resize_now():
            node = that.node
            # todo: formalize our event object
            event = {'cause': 'window'}  # owner and type set in Mirrored
            event.widthChanged = (that._stored_size[0] != node.offsetWidth)
            event.heightChanged = (that._stored_size[1] != node.offsetHeight)
            if event.widthChanged or event.heightChanged:
                that._stored_size = node.offsetWidth, node.offsetHeight
                that.emit_event('resize', event)
        self._check_resize = _check_resize
        self._check_resize()
    
    @js
    def _js_create_node(self):
        this.node = document.createElement('div')
    
    @js
    def _js_cssClassName_changed(self, name, old, className):
        this.node.className = className
    
    ## Children and parent
    
    @property
    def children(self):
        return self._children
    
    def _add_child(self, widget):
        pass
    
    def _remove_child(self, widget):
        pass
    
    @js
    def _js_add_child(self, widget):
        """ Add the DOM element. Called right after the child widget is added. """
        # May be overloaded in layout widgets
        self.node.appendChild(widget.node)
    
    @js
    def _js_remove_child(self, widget):
        """ Remove the DOM element. Called right after the child widget is removed. """
        self.node.removeChild(widget.node)
    
    def _parent_changed(self, name, old_parent, new_parent):
        if old_parent is not None:
            children = list(old_parent.children)
            while self in children:
                children.remove(self)
            #old_parent._set_prop('children', children)  # bypass readonly
            old_parent._children = tuple(children)
            old_parent._remove_child(self)
        if new_parent is not None:
            children = list(new_parent.children)
            children.append(self)
            #new_parent._set_prop('children', children)
            new_parent._children = tuple(children)
            new_parent._add_child(self)
    
    @js
    def _js_parent_changed(self, name, old_parent, new_parent):
        if old_parent is not None:
            children = old_parent.children
            while self in children:
                children.remove(self)
            old_parent._remove_child(self)
        if new_parent is not None:
            children = new_parent.children
            children.append(self)
            new_parent._add_child(self)
        # Unregister events
        if old_parent is None:
            window.removeEventListener('resize', self._check_resize, False)
        else:
            old_parent.disconnect_event('resize', self._check_resize)
        # Register events
        if new_parent is None:
            window.addEventListener('resize', self._check_resize, False)
        else:
            new_parent.connect_event('resize', self._check_resize)
    
    ## Positionion
    
    @js
    def _js_pos_changed(self, name, old, pos):
        self.node.style.left = pos[0] + "px" if (pos[0] > 1) else pos[0] * 100 + "%"
        self.node.style.top = pos[1] + "px" if (pos[1] > 1) else pos[1] * 100 + "%"
    
    @js
    def _js_size_changed(self, name, old, size):
        size = size[:]
        for i in range(2):
            if size[i] == 0 or size is None or size is undefined:
                size[i] = ''  # Use size defined by CSS
            elif size[i] > 1:
                size[i] = size[i] + 'px'
            else:
                size[i] = size[i] * 100 + 'px'
        self.node.style.width = size[0]
        self.node.style.height = size[1]
    
    ## More 
    
    @js
    def _js_set_cointainer_id(self, id):
        #if self._parent:
        #    return
        print('setting container id', id)
        el = document.getElementById(id)
        el.appendChild(this.node)
    
    def _repr_html_(self):
        container_id = self.id + '_container'
        # Set container id, this gets applied in the next event loop
        # iteration, so by the time it gets called in JS, the div that
        # we define below will have been created.
        from .app import call_later
        call_later(0, self.set_cointainer_id, container_id) # todo: always do calls in next iter
        return "<div id=%s />" % container_id
