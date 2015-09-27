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
from ..app import Pair, get_instance_by_id, no_sync
from ..app.serialize import serializer
from ..react import undefined


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


class Element(Pair):
    """ Object that represents an HTML element.
    """
    pass  # todo: to e.g. have <b> and <p> objects


class Widget(Pair):
    """ Base widget class.
    
    In HTML this represents a plain div-element.

    When *subclassing* a Widget to create a compound widget (a widget
    that serves as a container for other widgets), use the ``init()``
    method to initialize child widgets. This method is called while
    the widget is the current widget.
    
    When subclassing to create a custom widget use the ``_init()``
    method both for the Python and JS version of the class.
    
    """
    
    def __init__(self, **kwargs):
        # todo: -> parent is widget or ref to div element
        
        # Apply default parent?
        parent = kwargs.pop('parent', None)
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
    def parent(self, new_parent=None):
        """ The parent widget, or None if it has no parent.
        """
        # A note on how we do parenting: The parent and children signals
        # are mutually dependent; changing either will also change the
        # other (though on another widget). To prevent an infinite loop
        # we use the feature that we can set other signals directly
        # from the input function: while we are inside this function,
        # the signal is "locked". In JS we perform the exact same trick.
        # To sync Python and JS, we only sync the parent signal,
        # otherwise we'd create a loop. We use the ``no_sync``
        # decorator. In the end, we can set the parent and children
        # signal, and the other signal is updated immediately. This
        # works in JS and Py.
        
        old_parent = self.parent._value  # has not been set yet
        
        if new_parent is old_parent:
            return undefined
        if not (new_parent is None or isinstance(new_parent, Widget)):
            raise ValueError('parent must be a widget or None')
        
        if old_parent is undefined:
            return new_parent
        
        if old_parent is not None:
            children = list(old_parent.children())
            while self in children:
                children.remove(self)
            old_parent.children._set(children)
        if new_parent is not None:
            children = list(new_parent.children())
            children.append(self)
            new_parent.children._set(children)
        
        return new_parent
    
    @no_sync
    @react.input
    def children(self, new_children=()):
        """ The child widgets of this widget.
        """
        old_children = self.children._value
        
        if new_children == old_children:
            return undefined
        if not all([isinstance(w, Widget) for w in new_children]):
            raise ValueError('All children must be widget objects.')
        
        if old_children is not undefined:
            for child in old_children:
                if child not in new_children:
                    child.parent(None)
        for child in new_children:
            child.parent(self)
        
        return tuple(new_children)
    
    @react.input
    def title(v=''):
        """ The title of this widget. This can be used to mark the
        widget in e.g. a tab layout or form layout.
        """
        return str(v)
    
    @react.input
    def flex(v=0):
        """ How much space this widget takes when contained in a
        flexible layout such as Box or FormLayout. A flex of 0 means
        to take the minimum size.
        """
        if isinstance(v, (int, float)):
            v = v, v
        return _check_two_scalars('flex', v)
    
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
    def style(v=''):
        """ CSS style options for this widget object. e.g. 
        ``"background: #f00; color: #0f0;"``. If the given value is a
        dict, its key-value pairs are converted to a CSS style string.
        Note that the CSS class attribute can be used to style all
        instances of a class.
        """
        if isinstance(v, dict):
            v = '; '.join('%s: s%' % (k, v) for k, v in v.items())
        return str(v)
    
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
            self.node = self.p.node
            
            that = this
            class SizeNotifier:
                def filterMessage(handler, msg):
                    if msg._type == 'resize':
                        that._update_actual_size()
                    return False
            if self.p:
                phosphor.messaging.installMessageFilter(self.p, SizeNotifier())
            
            #flexx.get('body').appendChild(this.node)
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
            
            super()._init()
        
        # todo: rename to current_size
        # todo: its hard to keep track of this reliably. a Button in an hbox can change size when the text of another button changes.
        # todo: maybe actual_size should be something for layouts only? though they suffer from same limitations
        @react.source
        def actual_size(v=(0, 0)):
            """ The real (actual) size of the widget.
            """
            return v[0], v[1]
        
        @react.connect('parent', 'container_id')
        def __update_actual_size(self, p, c):
            self._update_actual_size()
        
        def _update_actual_size(self):
            n = self.node
            cursize = self.actual_size()
            if cursize[0] != n.offsetWidth or cursize[1] !=n.offsetHeight:
                self.actual_size._set([n.offsetWidth, n.offsetHeight])
        
        def _create_node(self):
            self.p = phosphor.createWidget('div')
        
        @react.input
        def parent(self, new_parent):  # note: no default value
            old_parent = self.parent._value
            
            if new_parent is old_parent:
                return undefined
            if not (new_parent is None or new_parent.__signals__):
               raise ValueError('parent must be a widget or None')
            
            if old_parent is undefined:
                return new_parent
            
            if old_parent is not None:
                children = list(old_parent.children())
                while self in children:
                    children.remove(self)
                old_parent.children._set(children)
            if new_parent is not None:
                children = list(new_parent.children())
                children.append(self)
                new_parent.children._set(children)
            
            return new_parent
        
        @no_sync
        @react.input
        def children(self, new_children=()):
            old_children = self.children._value
            
            # todo: PyScript support deep comparisons
            #if new_children == old_children:
            #    return undefined
            if old_children is not undefined and len(new_children) == len(old_children):
                for i in range(len(new_children)):
                    if new_children[i] != old_children[i]:
                        break
                else:
                    return undefined
            
            if not all([bool(w.__signals__) for w in new_children]):
                raise ValueError('All children must be widget objects.')
            
            if old_children is not undefined:
                for child in old_children:
                    if child not in new_children:
                        child.parent(None)
            for child in new_children:
                child.parent(self)
            
            return tuple(new_children)
        
        @react.connect('children')
        def __children_changed(self, new_children):
            old_children = self.children.last_value
            if not old_children:
                old_children = []
            
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
            """ Add the DOM element. Called right after the child widget is added. """
            self.p.addChild(widget.p)
            
            # # May be overloaded in layout widgets
            # if self.p and widget.p:
            #     self.p.addChild(widget.p)
            # elif 1:# self.p:  # need_phosphor_children
            #     widget.proxy_p = phosphor.widget.Widget()
            #     widget.proxy_p.node.appendChild(widget.node)
            #     self.p.addChild(widget.proxy_p)
            # elif widget.p:
            #     raise RuntimeError('A Phosphor widget cannot be a child of a common widget.')
            # else:
            #     self.node.appendChild(widget.node)
        
        def _remove_child(self, widget):
            """ Remove the DOM element. Called right after the child widget is removed. """
            self.p.removeChild(widget.p)
            
            # if self.p and widget.p:
            #     self.p.removeChild(widget.p)
            # elif 1:# self.p:
            #     self.p.removeChild(widget.proxy_p)
            #     widget.proxy_p.dispose()
            #     del widget.proxy_p
            # elif widget.p:
            #     raise RuntimeError('What? A Phosphor widget cannot be a child of a common widget.')
            # else:
            #     self.node.removeChild(widget.node)
        
        # @react.connect('pos')
        # def _pos_changed(self, pos):
        #     # todo: a layout that uses this can connect to the signal and set the style. we should not. same for size
        #     self.p.node.style.left = pos[0] + "px" if (pos[0] > 1) else pos[0] * 100 + "%"
        #     self.p.node.style.top = pos[1] + "px" if (pos[1] > 1) else pos[1] * 100 + "%"
       
        @react.connect('style')
        def __stye_changed(self, style):
            #self.node.style = style  # forbidden in strict mode, plus it clears all previously set style
            for part in style.split(';'):
                if ':' in part:
                    key, val = part.split(':')
                    key, val = key.trim(), val.trim()
                    self.node.style[key] = val
        
        @react.connect('container_id')
        def _container_id_changed(self, id):
            #if self._parent:
            #    return
            if id:
                el = document.getElementById(id)
                if self.p:
                    if self.p.isAttached:
                        phosphor.widget.detachWidget(self.p)
                    phosphor.widget.attachWidget(self.p, el)
                    p = self.p
                    window.addEventListener('resize', lambda:p.update())
                else:
                    el.appendChild(this.p.node)
            if id == 'body':
                self.p.node.classList.add('flx-main-widget')
