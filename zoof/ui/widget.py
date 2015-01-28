
from .app import App


class NativeElement(object):
    
    def __init__(self, id):
        t = 'document.getElementById("{id}").innerHTML = "{text}"'
        # ... get __dir__ from JS and allow live inspection of DOM elements
        # That would be great for debugging ...


class Widget(object):
    _counter = 0
    def __init__(self, parent):
        self._parent = parent
        
        #
    
    def _create(self, app):
        
        if self._parent is None:
            win = self._app._new_window()


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
    
    def __init__(self, parent, text='Click me'):
        Widget._counter += 1
        self._parent = parent
        self._id = 'but%i' % Widget._counter
        self._text = text
        if parent._ws:
            self._create()
    
    def set_text(self, text):
        self._text = text
        if self._parent._ws:
            t = 'document.getElementById("{id}").innerHTML = "{text}"'
            self._parent.eval(t.format(id=self._id, text=text))
    
    def _create(self):
        self._parent.eval(self._TEMPLATE.format(id=self._id, text=self._text))
        

