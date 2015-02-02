
from .app import App, BaseWidget


class NativeElement(object):
    
    def __init__(self, id):
        t = 'document.getElementById("{id}").innerHTML = "{text}"'
        # ... get __dir__ from JS and allow live inspection of DOM elements
        # That would be great for debugging ...


class Widget(BaseWidget):
    _counter = 0
    def __init__(self, parent, flex=0):
        assert parent is not None
        BaseWidget.__init__(self, parent)
        self._flex = flex
        app = self.get_app()
        app._widget_counter += 1
        self._id = self.__class__.__name__ + str(app._widget_counter)
    
    def get_app(self):
        node = self.parent
        while not isinstance(node, App):
            node = node.parent
        return node
    
    def _create(self, app):
        pass
    
    @property
    def id(self):
        return self._id
    


class Window(object):
    
    __slots__ = ['_title', '_parent']
    
    _TEMPLATE = """
        window.win{id} = window.open('{url}', '_blank', '{specs}');
        """
    
    def __init__(self, parent, title='new window'):
        assert isinstance(parent, App)
        self._parent = parent
        self._title = title
        if parent._ws:
            self._create()
    
    def _create(self):
        t = self._TEMPLATE.format(id=id(self), url='about:blank', specs='')
        print(t)
        # arg, this needs to go in an onload
        t += '\nwindow.win{id}.document.body.innerHTML = "";'.format(id=id(self))
        self._parent.eval(t)
    
    def close(self):
        self._parent.eval('window.win{id}.close()'.format(id=id(self)))
        
    def set_title(self, title):
        pass
        # todo: properties or functions?


class Label(Widget):
    pass


class Button(Widget):
    _TEMPLATE = """
        var e = document.createElement("button");
        e.id = '{id}';
        e.innerHTML = '{text}'
        document.body.appendChild(e);
        """
    
    def __init__(self, parent, text='Click me', **kwargs):
        super().__init__(parent, **kwargs)
        Widget._counter += 1
        self._text = text
        if self.get_app()._ws:
            self._create()
    
    def set_text(self, text):
        self._text = text
        if self._parent._ws:
            t = 'document.getElementById("{id}").innerHTML = "{text}"'
            self._parent.eval(t.format(id=self._id, text=text))
    
    def _create(self):
        eval = self.get_app().eval
        #self._parent.eval(self._TEMPLATE.format(id=self._id, text=self._text))
        parent = 'body' if isinstance(self.parent, App) else self.parent.id
        T = 'zoof.createButton("{parent}", "{id}", "{text}");'
        eval(T.format(parent=parent, id=self._id, text=self._text))
        eval('zoof.setProps("{id}", "flex", {flex});'.format(id=self.id, flex=self._flex))
        for child in self.children:
            child._create()
        

class HBoxLayout(Widget):
    
    def __init__(self, parent):
        super().__init__(parent)
        self._need_update = False
        if parent._ws:
            self._create()
    
    def _create(self):
        eval = self.get_app().eval
        #self._parent.eval(self._TEMPLATE.format(id=self._id, text=self._text))
        T = 'zoof.createHBoxLayout("body", "{id}");'
        eval(T.format(id=self._id))
        for child in self.children:
            child._create()
        if self._need_update:
            self._need_update = False
            self.update()
    
    def update(self):
        eval = self.get_app().eval
        if self.get_app()._ws:
            eval('zoof.HBoxLayout_layout("{id}");'.format(id=self._id))
        else:
            self._need_update = True
