""" The base widget class.

Implements parenting and other things common to all widgets.
"""

import json
import threading

from ..pyscript import js
from .. import react
from . import Pair, get_instance_by_id


def _check_two_scalars(name, v):
    if not (isinstance(v, (list, tuple)) and
            isinstance(v[0], (int, float)) and
            isinstance(v[1], (int, float))):
        raise ValueError('%s must be a tuple of two scalars.' % name)
    return float(v[0]), float(v[1])


class WidgetProp:
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
class WidgetsProp:
    
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
        tid = id(threading.current_thread())
    else:
        tid = id(threading.currentThread())
    # Get list of parents for this thread
    return _default_parents_per_thread.setdefault(tid, [])


class Widget(Pair):
    """ Base widget class.
    
    In HTML-speak, this represents a plain div-element. Not very useful
    on itself, except perhaps to fill up space. Subclass to create something
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
    
    def __init__(self, parent=None, **kwargs):
        # todo: -> parent is widget or ref to div element
        
        # Apply default parent?
        if parent is None:
            default_parents = _get_default_parents()
            if default_parents:
                parent = default_parents[-1]
        
        # Use parent proxy unless proxy was given
        if parent is not None and not kwargs.get('_proxy', None):
            kwargs['_proxy'] = parent.proxy
        
        # Provide css class name to 
        classes = ['flx-' + c.__name__.lower() for c in self.__class__.mro()]
        classname = ' '.join(classes[:1-len(Widget.mro())])
        
        # Pass properties via kwargs
        kwargs['_css_class_name'] = classname
        kwargs['parent'] = parent
        Pair.__init__(self, **kwargs)
        
        with self:
            self.init()
    
    def _repr_html_(self):
        """ This is to get the widget shown inline in the notebook.
        """
        if self.container_id:
            return "<i>This widget is already shown in this notebook</i>"
        
        container_id = self.id + '_container'
        def set_cointainer_id():
            self.container_id = container_id
        # Set container id, this gets applied in the next event loop
        # iteration, so by the time it gets called in JS, the div that
        # we define below will have been created.
        from ..pair import call_later
        call_later(0.1, set_cointainer_id) # todo: always do calls in next iter
        return "<div class='flx-container' id=%s />" % container_id
    
    def init(self):
        """ Overload this to initialize a cusom widget. Inside, this
        widget is the current parent.
        """
        pass
    
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
    
    @react.source
    def container_id(v=''):
        """ The id of the DOM element that contains this widget if
        parent is None.
        """
        return str(v)
    
    @react.input
    def parent(v=None):
        """ The parent widget, or None if it has no parent.
        """
        if v is None or isinstance(v, Widget):
            return v
        else:
            raise ValueError('parent must be a widget or None')
    
    @react.input
    def flex(v=0):
        """ How much space this widget takes when contained in a layout.
        A flex of 0 means to take the minimum size.
        """
        return float(v)
    
    @react.input
    def pos(v=(0, 0)):
        """ The position of the widget when it in a ayout that allows
        positioning.
        """
        return _check_two_scalars('pos', v)
    
    @react.input
    def size(v=(0, 0)):
        """ The size of the widget when it in a ayout that allows
        positioning.
        """
        return _check_two_scalars('size', v)
    
    @react.input
    def min_size(v=(0, 0)):
        """ The minimum size of the widget.
        """
        return _check_two_scalars('min_size', v)
    
    # todo: can we calculate this in JS somehow?
    @react.input
    def _css_class_name(self, v=''):
        v = str(v)
        if getattr(self, '_IS_MAIN_WIDGET', False):  # set when a widget is made into an app
            v = 'flx-main-widget ' + v
        return v
    
    
    CSS = """
    
    .flx-container {
        min-height: 10px; /* splitter sets its own minsize if contained */
    }
    
    .flx-widget {
        box-sizing: border-box;
        white-space: nowrap;
        overflow: hidden;
    }
    
    .flx-main-widget {
       width: 100%;
       height: 100%;
    }
    
    """
    
    class JS:
        
        def __init__(self):
            super().__init__()
            
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
                event = {'cause': 'window'}
                event.widthChanged = (that._stored_size[0] != node.offsetWidth)
                event.heightChanged = (that._stored_size[1] != node.offsetHeight)
                if event.widthChanged or event.heightChanged:
                    that.real_size._set([node.offsetWidth, node.offsetHeight])
            self._check_resize = _check_resize
            self._check_resize()
        
        @react.source
        def children(v=()):
            """ The child widgets of this widget.
            """
            for w in v:
                if not isinstance(w, flexx.classes.Widget):
                    raise ValueError('Children should be Widget objects.')
            return v
            
        @react.source
        def real_size(v=(0, 0)):
            """ The real (actual) size of the widget.
            """
            return v[0], v[1]
        
        def _create_node(self):
            this.node = document.createElement('div')
        
        @react.act('_css_class_name')
        def _css_class_name_changed(self, v):
            this.node.className = v
        
        def _add_child(self, widget):
            """ Add the DOM element. Called right after the child widget is added. """
            # May be overloaded in layout widgets
            self.node.appendChild(widget.node)
        
        def _remove_child(self, widget):
            """ Remove the DOM element. Called right after the child widget is removed. """
            self.node.removeChild(widget.node)
        
        @react.act('parent')
        def _parent_changed(self, new_parent):
            old_parent = self.parent.last_value
            if old_parent is not None:
                children = old_parent.children()[:]
                while self in children:
                    children.remove(self)
                old_parent.children._set(children)
                old_parent._remove_child(self)
            if new_parent is not None:
                children = new_parent.children()[:]
                children.append(self)
                new_parent.children._set(children)
                new_parent._add_child(self)
            
            # re-connect size-signal
            # todo: no need if we have dynamism
            #self._keep_size_up_to_date.connect(False)
            
            
            # # Unregister events
            # if old_parent is None:
            #     window.removeEventListener('resize', self._check_resize, False)
            # else:
            #     old_parent.disconnect_event('resize', self._check_resize)
            # # Register events
            # if new_parent is None:
            #     window.addEventListener('resize', self._check_resize, False)
            # else:
            #     new_parent.connect_event('resize', self._check_resize)
        
        #@react.act('parent.real_size')
        #def _keep_size_up_to_date(size):
        #    self._check_resize()
        
        @react.act('pos')
        def _pos_changed(self, pos):
            self.node.style.left = pos[0] + "px" if (pos[0] > 1) else pos[0] * 100 + "%"
            self.node.style.top = pos[1] + "px" if (pos[1] > 1) else pos[1] * 100 + "%"
        
        @react.act('size')
        def _size_changed(self, size):
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
        
        @react.act('container_id')
        def _container_id_changed(self, id):
            #if self._parent:
            #    return
            if id:
                el = document.getElementById(id)
                el.appendChild(this.node)
                self._check_resize()
    
    ## Children and parent
    
    # @property
    # def children(self):
    #     return self._children
    # 
    # def _add_child(self, widget):
    #     pass  # special hook to introduce a child inside this widget
    # 
    # def _remove_child(self, widget):
    #     pass  # special hook to remove a child out from this widget
    # 
    # 
    # @react.act('parent')
    # def _parent_changed(self, new_parent):
    #     old_parent = self.parent.previous_value
    #     if old_parent is not None:
    #         children = list(old_parent.children())
    #         while self in children:
    #             children.remove(self)
    #         #old_parent._set_prop('children', children)  # bypass readonly
    #         old_parent.children._set(children)
    #         old_parent._remove_child(self)
    #     if new_parent is not None:
    #         children = list(new_parent.children())
    #         children.append(self)
    #         #new_parent._set_prop('children', children)
    #         new_parent.children._set(children)
    #         new_parent._add_child(self)
    
