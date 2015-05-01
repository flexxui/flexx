import json

from ..pyscript import js
from ..properties import Prop, Instance, Str, Tuple
from .mirrored import Mirrored, get_instance_by_id


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
        return flexx.widgets[JSON.parse(value)]


class Widget(Mirrored):
    """ Base widget class.
    """
    
    CSS = """
    
    """
    
    parent = WidgetProp()
    children = Tuple(WidgetProp)  # todo: can we make this readonly?
    
    container_id = Str()  # used if parent is None
    
    def __init__(self, parent=None):
        # todo: -> parent is widget or ref to div element
        Mirrored.__init__(self)
        
        self.parent = parent
        
        classes = ['zf-' + c.__name__.lower() for c in self.__class__.mro()]
        classes = ' '.join(classes[:1-len(Widget.mro())])
        #self._js_init(classes)  # todo: allow a js __init__
    
    @js
    def _js_init(self):
        pass
    
    def _parent_changed(self, name, old_parent, new_parent):
        print('setting parent in Py')
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
    def _parent_changed__js(self, name, old_parent, new_parent):
        print('setting parent in JS')
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
    
    @js
    def set_cointainer_id(self, id):
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


class Button(Widget):
    
    CSS = """
    .zf-button {
        background: #fee;
    }
    """
    
    text = Str('push me')
    
    def __init__(self):
        Mirrored.__init__(self)
        #self._js_init()  # todo: allow a js __init__
    
    @js
    def _jsinit(self, className):
        # todo: allow setting a placeholder DOM element, or any widget parent
        this.node = document.createElement('button')
        this.node.className = className
        flexx.get('body').appendChild(this.node);
        this.node.innerHTML = 'Look, a button!'
    
    @js
    def _text_changed__js(self, name, old, txt):
        print('_set_text', txt)
        this.node.innerHTML = txt


class Label(Widget):
    CSS = ".zf-label { border: 1px solid #454; }"

    text = Str()
    
    @js
    def _jsinit(self, className='zf-Label zf-Widget'):
        # todo: allow setting a placeholder DOM element, or any widget parent
        this.node = document.createElement('div')
        this.node.className = className
        flexx.get('body').appendChild(this.node);
        this.node.innerHTML = 'a label'
    
    @js
    def _text_changed__js(self, name, old, txt):
        this.node.innerHTML = txt


class Layout(Widget):
    CSS = """
    
    .zf-layout {
    
    }
    """
    
    @js
    def _js_init(self, className='zf-Button zf-Widget'):
        # todo: allow setting a placeholder DOM element, or any widget parent
        this.node = document.createElement('div')
        this.node.className = className
        flexx.get('body').appendChild(this.node);
    
    
class HBox(Layout):
    
    @js
    def _js_init(self, className):
        pass

    
