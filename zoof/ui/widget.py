
import json

from .app import App, BaseWidget


class NativeElement(object):
    
    def __init__(self, id):
        t = 'document.getElementById("{id}").innerHTML = "{text}"'
        # ... get __dir__ from JS and allow live inspection of DOM elements
        # That would be great for debugging ...


class Widget(BaseWidget):
    """ Base widget class
    
    All widgets derive from this class. On itself, this type of widget
    represents an empty space, and can be useful as a filler.
    """
    
    _counter = 0  # to produce unique id's
    
    def __init__(self, parent=None, flex=0):
        if parent is None:
            if _default_parent:
                parent = _default_parent[-1]
            else:
                raise ValueError('Parent must be given unless it is '
                                 'instantiated a widget context.')
        BaseWidget.__init__(self, parent)
        self._flex = flex
        app = self.get_app()
        app._widget_counter += 1
        self._id = self.__class__.__name__ + str(app._widget_counter)
        
        # Call function to create js_object
        self._create_js_object()
    
    def _create_js_object(self, **kwargs):
        """ This method can be overloaded to populate the dict used
        by JS to create the widget. Overloaded versions should simpy
        call the super-method with additional kwargs.
        """
        
        # Get css classes
        classes = ['zf-' + c.__name__.lower() for c in self.__class__.mro()]
        classes = ' '.join(classes[:1-len(Widget.mro())])
        
        # Get parent
        parent = 'body' if isinstance(self.parent, App) else self.parent.id
        
        self._create_js_object_real(id=self.id, 
                                    className=classes, 
                                    parent=parent, 
                                    **kwargs)
        
    def _create_js_object_real(self, **kwargs):
        
        eval = self.get_app()._exec
        funcname = 'create' + self.__class__.__name__
        eval('zoof.%s(%s);' % (funcname, json.dumps(kwargs)))
        eval('zoof.setProps("%s", "flex", %s);' % (self.id, self._flex))
    
    def get_app(self):
        node = self.parent
        while not isinstance(node, App):
            node = node.parent
        return node
    
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
        self._parent._exec(t)
    
    def close(self):
        self._parent._exec('window.win{id}.close()'.format(id=id(self)))
        
    def set_title(self, title):
        pass
        # todo: properties or functions?


class Label(Widget):
    """ A Label represents a piece of text.
    """
    
    def __init__(self, parent=None, text='', **kwargs):
        self._text = text
        super().__init__(parent, **kwargs)
    
    def _create_js_object_real(self, **kwargs):
        super()._create_js_object_real(text=self._text, **kwargs)
        
    def set_text(self, text):
        self._text = text
        t = 'document.getElementById("{id}").innerHTML = "{text}"'
        self.get_app()._exec(t.format(id=self._id, text=text))


class Button(Widget):
    """ A Button is a widget than can be clicked on to invoke an action
    """
    
    def __init__(self, parent=None, text='Click me', **kwargs):
        self._text = text
        super().__init__(parent, **kwargs)
    
    def _create_js_object_real(self, **kwargs):
        super()._create_js_object_real(text=self._text, **kwargs)
    
    def set_text(self, text):
        self._text = text
        t = 'document.getElementById("{id}").innerHTML = "{text}"'
        self.get_app()._exec(t.format(id=self._id, text=text))


_default_parent = []


class Layout(Widget):
    """ Base class for all layouts
    """


class HBox(Layout):
    """ An HBox is a layout widget used to align widgets horizontally
    """
    
    def __init__(self, parent=None, spacing=None, margin=None, **kwargs):
        self._spacing = spacing
        self._margin = margin
        
        super().__init__(parent, **kwargs)
    
    def _create_js_object_real(self, **kwargs):
        spacing = str(self._spacing or 0) + 'px'
        margin = str(self._margin or 0) + 'px'
        super()._create_js_object_real(spacing=spacing, margin=margin, **kwargs)
    
    def update(self):
        eval = self.get_app()._exec
        eval('zoof.HBox_layout("{id}");'.format(id=self._id))
    
    def __enter__(self):
        _default_parent.append(self)
        return self
    
    def __exit__(self, type, value, traceback):
        assert self is _default_parent.pop(-1)
        if value is None:
            self.update()


class VBox(Layout):
    """ An VBox is a layout widget used to align widgets vertically
    """
    
    def __init__(self, parent=None, **kwargs):
        super().__init__(parent, **kwargs)
    
    def update(self):
        eval = self.get_app()._exec
        eval('zoof.VBox_layout("{id}");'.format(id=self._id))
    
    def __enter__(self):
        _default_parent.append(self)
        return self
    
    def __exit__(self, type, value, traceback):
        assert self is _default_parent.pop(-1)
        if value is None:
            self.update()
