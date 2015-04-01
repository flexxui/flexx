from .mirrored import Mirrored, Instance, Str, Tuple, js



class Widget(Mirrored):
    
    CSS = """
    
    """
    
    parent = Instance(Mirrored)  # todo: can we set our own class?
    children = Tuple(Mirrored)  # todo: can we make this readonly?
    
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
    def _set_text(self, txt):
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

    
