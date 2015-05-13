import json

from ..pyscript import js
from ..properties import Prop, Instance, Str, Tuple, Float
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
    
    container_id = Str()  # used if parent is None
    
    parent = WidgetProp()
    #children = Tuple(WidgetProp)  # todo: can we make this readonly?
    children = WidgetsProp()
    
    flex = Float()
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
        
        #self._js_init(classes)  # todo: allow a js __init__
    
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
    def _parent_changed__js(self, name, old_parent, new_parent):
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
    
    # def __init__(self):
    #     Mirrored.__init__(self)
    #     #self._js_init()  # todo: allow a js __init__
    
    @js
    def _js_init(self):
        # todo: allow setting a placeholder DOM element, or any widget parent
        this.node = document.createElement('button')
        #this.node.className = this.cssClassName
        flexx.get('body').appendChild(this.node);
        this.node.innerHTML = 'Look, a button!'
    
    @js
    def _text_changed__js(self, name, old, txt):
        this.node.innerHTML = txt


class Label(Widget):
    CSS = ".zf-label { border: 1px solid #454; }"

    text = Str()
    
    @js
    def _js_init(self):
        # todo: allow setting a placeholder DOM element, or any widget parent
        this.node = document.createElement('div')
        #this.node.className = this.cssClassName
        flexx.get('body').appendChild(this.node);
        this.node.innerHTML = 'a label'
    
    @js
    def _text_changed__js(self, name, old, txt):
        this.node.innerHTML = txt


class Layout(Widget):
    CSS = """
    
    .zf-layout {
        width: 100%;
        height: 100%;
        margin: 0px;
        padding: 0px;
        border-spacing: 0px;
        border: 0px;
    }
    
    .zf-layout > .zf-layout {
        /* A layout in a layout need to adjust using "natural size" or min-size.  */
        width: auto;
        height: auto;
    }
    
    .hcell .vcell {
        /* inter-widget spacing. padding-left/top is set to "spacing"
        on each non-first row/column in the layout. */
        padding: 0px;  
    }
    """
    
    @js
    def _js_applyBoxStyle(self, e, sty, value):
        for prefix in ['-webkit-', '-ms-', '-moz-', '']:
            e.style[prefix + sty] = value


class Box(Layout):
    
    CSS = """
    .zf-hbox, .zf-vbox {
        display: -webkit-flex;
        display: -ms-flexbox;  /* IE 10 */
        display: -ms-flex;     /* IE 11 */
        display: -moz-flex;
        display: flex;
        
        justify-content: stretch;  /* start, end, center, space-between, space-around * /
        align-items: stretch;
        align-content: stretch;
    }
    
    */
    .box-align-center { -webkit-align-items: center; -ms-align-items: center; -moz-align-items: center; align-items: center; }
    .box-align-center { -webkit-align-items: center; -ms-align-items: center; -moz-align-items: center; align-items: center; }
    */
    
    .zf-hbox > .zf-hbox, .zf-hbox > .zf-vbox {
        width: auto;
    }
    .zf-vbox > .zf-hbox, .zf-vbox > .zf-vbox {
        height: auto;
    }
    """
    
    @js
    def _js_init(self):
        this.node = document.createElement('div')
        #this.node.className = self.cssClassName
        flexx.get('body').appendChild(this.node);
    
    @js
    def _js_set_child(self, el):
        self._applyBoxStyle(el.node, 'flex-grow', el.flex)
        super()._set_child(el)


class HBox(Box):
    
    CSS = """
    .zf-hbox {
        -webkit-flex-flow: row;
        -ms-flex-flow: row;
        -moz-flex-flow: row;
        flex-flow: row;
        /*border: 1px dashed #44e;*/
        width: 100%;
    }
    """

class VBox(Box):
    CSS = """
    .zf-vbox {
        -webkit-flex-flow: column;
        -ms-flex-flow: column;
        -moz-flex-flow: column;
        flex-flow: column;
        /*border: 1px dashed #e44;*/
        height: 100%;
        width: 100%;
    }
    """
