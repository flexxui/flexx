"""
.. UIExample:: 100
    
    from flexx import app, ui
    
    # A red widget
    class Example(ui.Widget):
        CSS = ".flx-example {background:#f00; min-width: 20px; min-height:20px}"

"""

import json
import threading

from .. import react
from ..app import Pair, get_instance_by_id
from ..app.serialize import serializer


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


class Widget(Pair):
    """ Base widget class.
    
    In HTML-speak, this represents a plain div-element. Not very useful
    on itself, except perhaps to fill up space. Subclass to create
    something interesting.

    When *subclassing* a Widget to create a compound widget (a widget
    that serves as a container for other widgets), use the ``init()``
    method to initialize child widgets. This method is called while
    the widget is the current widget.
    
    When subclassing to create a custom widget use the ``_init()``
    method both for the Python and JS version of the class.
    
    """
    
    def __init__(self, **kwargs):
        # todo: -> parent is widget or ref to div element
        
        parent = kwargs.pop('parent', None)
        # Apply default parent?
        if parent is None:
            default_parents = _get_default_parents()
            if default_parents:
                parent = default_parents[-1]
        
        # Use parent proxy unless proxy was given
        if parent is not None and not kwargs.get('_proxy', None):
            kwargs['proxy'] = parent.proxy
        
        # Pass properties via kwargs
        kwargs['parent'] = parent
        Pair.__init__(self, **kwargs)
        
        with self:
            self.init()
        
        # Signal dependencies may have been added during init(), also in JS
        self.connect_signals(False)
        cmd = 'flexx.instances.%s.connect_signals(false);' % self._id
        self._proxy._exec(cmd)
    
    def _repr_html_(self):
        """ This is to get the widget shown inline in the notebook.
        """
        if self.container_id():
            return "<i>This widget is already shown in this notebook</i>"
        
        container_id = self.id + '_container'
        def set_cointainer_id():
            self.container_id._set(container_id)
        # Set container id, this gets applied in the next event loop
        # iteration, so by the time it gets called in JS, the div that
        # we define below will have been created.
        from ..app import call_later
        call_later(0.1, set_cointainer_id) # todo: always do calls in next iter
        return "<div class='flx-container' id=%s />" % container_id
    
    def init(self):
        """ Overload this to initialize a cusom widget. Inside, this
        widget is the current parent.
        """
        pass
    
    def disconnect_signals(self, *args):
        """ Overloaded version of disconnect_signals() that will also
        disconnect the signals of any child widgets.
        """
        children = self.children()
        Pair.disconnect_signals(self, *args)
        for child in children:
            child.disconnect_signals(*args)
    
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
    
    @react.input
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
    
    # Note that both the Py and JS have their own children signal
    # todo: prevent unnecesary updates
    @react.source
    def children(v=()):
        """ The child widgets of this widget.
        """
        assert all([isinstance(w, Widget) for w in v])
        return tuple(v)
    
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
        """ The size of the widget when it in a layout that allows
        positioning.
        """
        return _check_two_scalars('size', v)
    
    @react.input
    def min_size(v=(0, 0)):
        """ The minimum size of the widget.
        """
        return _check_two_scalars('min_size', v)
    
    @react.input
    def bgcolor(v=''):
        """ Background color of the widget. In general it is better to do
        styling via CSS.
        """
        return str(v)
    
    @react.connect('parent')
    def _parent_changed_py(self, new_parent):
        old_parent = self.parent.last_value
        if old_parent is not None:
            children = list(old_parent.children()[:])
            while self in children:
                children.remove(self)
            old_parent.children._set(children)
        if new_parent is not None:
            children = list(new_parent.children()[:])
            children.append(self)
            new_parent.children._set(children)
    
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
        
        def _init(self):
            self._create_node()
            flexx.get('body').appendChild(this.node)
            # todo: allow setting a placeholder DOM element, or any widget parent
            
            cls_name = self._class_name
            for i in range(32):  # i.e. a safe while-loop
                self.node.classList.add('flx-' + cls_name.toLowerCase())  # todo: remove lowercase
                cls = flexx.classes[cls_name]
                if not cls:
                    break
                cls_name = cls.prototype._base_class._class_name
                if not cls_name or cls_name == 'Pair':
                    break
            else:
                raise RuntimeError('Error while determining class names')
            
            # Create closure to check for size changes
            self._stored_size = 0, 0
            self._checking_size = False
            that = this
            def _check_resize():
                # Re-raise in next event loop iteration
                if not that._checking_size:
                    setTimeout(_check_resize_now, 0.001)
                    that._checking_size = True
            def _check_resize_now():
                that._checking_size = False
                node = that.node
                widthChanged = (that._stored_size[0] != node.offsetWidth)
                heightChanged = (that._stored_size[1] != node.offsetHeight)
                if widthChanged or heightChanged:
                    that.actual_size._set([node.offsetWidth, node.offsetHeight])
            self._check_resize = _check_resize
            self._check_resize()
            
            super()._init()
        
        # @react.source
        # def children(v=()):
        #     """ The child widgets of this widget.
        #     """
        #     for w in v:
        #         if not isinstance(w, flexx.classes.Widget):
        #             raise ValueError('Children should be Widget objects.')
        #     return v
        
        @react.source
        def actual_size(v=(0, 0)):
            """ The real (actual) size of the widget.
            """
            return v[0], v[1]
        
        def _create_node(self):
            this.node = document.createElement('div')
        
        def _add_child(self, widget):
            """ Add the DOM element. Called right after the child widget is added. """
            # May be overloaded in layout widgets
            self.node.appendChild(widget.node)
        
        def _remove_child(self, widget):
            """ Remove the DOM element. Called right after the child widget is removed. """
            self.node.removeChild(widget.node)
        
        @react.connect('parent')
        def _parent_changed(self, new_parent):
            old_parent = self.parent.last_value
            if old_parent is not None and old_parent is not undefined:
                children = old_parent.children()[:]
                while self in children:
                    children.remove(self)
                old_parent.children._set(children)  # we set it directly
                old_parent._remove_child(self)
            if new_parent is not None:
                children = new_parent.children()[:]
                children.append(self)
                new_parent.children._set(children)
                new_parent._add_child(self)
        
        @react.connect('parent.actual_size')
        def _keep_size_up_to_date1(self, size):
            #print(self._id, 'resize 1', size)
            self._check_resize()
        
        @react.connect('parent', 'container_id')
        def _keep_size_up_to_date2(self, parent, id):
            #print(self._id, 'resize2 ', parent, id)
            if parent is None:
                window.addEventListener('resize', self._check_resize, False)
            else:
                window.removeEventListener('resize', self._check_resize, False)
            self._check_resize()
        
        @react.connect('pos')
        def _pos_changed(self, pos):
            self.node.style.left = pos[0] + "px" if (pos[0] > 1) else pos[0] * 100 + "%"
            self.node.style.top = pos[1] + "px" if (pos[1] > 1) else pos[1] * 100 + "%"
        
        @react.connect('size')
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
        
        @react.connect('bgcolor')
        def _bgcolor_changed(self, color):
            self.node.style['background-color'] = color
        
        @react.connect('container_id')
        def _container_id_changed(self, id):
            #if self._parent:
            #    return
            if id:
                el = document.getElementById(id)
                el.appendChild(this.node)
            if id == 'body':
                self.node.classList.add('flx-main-widget')
    
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
    # @react.connect('parent')
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
    
