import json

from .mirrored import Prop, Mirrored, Instance, Str, Tuple, js, get_instance_by_id


class WidgetProp(Prop):
    _default = None
    
    def validate(self, val):
        if val is None or isinstance(val, Widget):
            return val
        else:
            raise ValueError('Prop %s must be a Widget or None, got %r' % 
                             (self.name, val.__class__.__name__))
    
    def to_json(self, value):
        # Widgets are kept track of via their id
        if value is None:
            return json.dumps(None)
        return json.dumps(value.id)
    
    def from_json(self, txt):
        return get_instance_by_id(json.loads(txt))


class Widget(Mirrored):
    
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
    
    # def _set_parent(self, new_parent):
    #     old_parent = self.parent
    #     if old_parent is not None:
    #         while self in old_parent.children:
    #             old_parent._children.remove(self)
    #     if new_parent is not None:
    #         new_parent._children.append(self)
    #     self._parent = new_parent
    
    # todo: oh crap, we need _js_set_parent() or something if we will allow _set_x in Python
    @js
    def _get_parent(self):  # In js we store it internally as the id
        if self._parent is None:
            return None
        return zoof.widgets[self._parent]  # todo: rename to index both in JS and Py
    
    @js
    def _set_parent(self, val):
        if val is None:
            return None
        elif val.toLowerCase is undefined:  # string (id) or object
            return val.id
        else:
            return val
    
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
    
    text = Str()
    
    def __init__(self):
        Mirrored.__init__(self)
        #self._js_init()  # todo: allow a js __init__
    
    @js
    def _jsinit(self, className):
        # todo: allow setting a placeholder DOM element, or any widget parent
        this.node = document.createElement('button')
        this.node.className = className
        zoof.get('body').appendChild(this.node);
        this.node.innerHTML = 'Look, a button!'
    
    @js
    def _set_text__js(self, txt):
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
        zoof.get('body').appendChild(this.node);
        this.node.innerHTML = 'a label'
    
    @js
    def _set_text(self, txt):
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
        zoof.get('body').appendChild(this.node);
    
    
class HBox(Layout):
    
    @js
    def _js_init(self, className):
        pass

    
