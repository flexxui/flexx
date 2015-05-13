""" The base widget class.

Implements parenting and other things common to all widgets.
"""

import json

from ..pyscript import js
from ..properties import Prop, Instance, Str, Tuple, Float
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


class Widget(Mirrored):
    """ Base widget class.
    """
    
    CSS = """
    
    """
    
    # Properties
    
    container_id = Str()  # used if parent is None
    
    parent = WidgetProp(help="The parent widget")
    #children = Tuple(WidgetProp)  # todo: can we make this readonly?
    children = WidgetsProp(help="A tuple of child widgets")
    flex = Float(help="How much space this widget takes when contained in a " + 
                 "layout. A flex of 0 means to take the minimum size.")
    min_width = Float()
    min_height = Float()  # todo: or min_size?
    cssClassName = Str()  # todo: should this be private? Or can we calculate it in JS?
    
    def __init__(self, parent=None, **kwargs):
        # todo: -> parent is widget or ref to div element
        
        # Provide css class name to 
        classes = ['zf-' + c.__name__.lower() for c in self.__class__.mro()]
        classname = ' '.join(classes[:1-len(Widget.mro())])
        
        # Pass properties via kwargs
        kwargs['cssClassName'] = classname
        kwargs['parent'] = parent
        
        Mirrored.__init__(self, **kwargs)
    
    @js
    def _js_cssClassName_changed(self, name, old, className):
        if this.node:
            this.node.className = className
    
    @js
    def _js_set_child(self, widget):
        # May be overloaded in layout widgets
        self.node.appendChild(widget.node)
    
    def _parent_changed(self, name, old_parent, new_parent):
        if old_parent is not None:
            children = list(old_parent.children)
            while self in children:
                children.remove(self)
            old_parent._set_prop('children', children)  # bypass readonly
        if new_parent is not None:
            children = list(new_parent.children)
            children.append(self)
            new_parent._set_prop('children', children)
    
    @js
    def _js_parent_changed(self, name, old_parent, new_parent):
        if old_parent is not None:
            children = old_parent.children
            while children.indexOf(self) >= 0:  # todo: "self in children"
                children.remove(self)
            #old_parent._set_prop('children', children)  # bypass readonly
            old_parent.children = children
        if new_parent is not None:
            children = new_parent.children
            children.append(self)
            #new_parent._set_prop('children', children)
            new_parent.children = children
            new_parent._set_child(self)
    
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
