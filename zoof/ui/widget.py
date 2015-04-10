
import json

from .app import App, get_default_app


class NativeElement(object):
    
    def __init__(self, id):
        t = 'document.getElementById("{id}").innerHTML = "{text}"'
        # ... get __dir__ from JS and allow live inspection of DOM elements
        # That would be great for debugging ...


class Widget(object):
    """ Base widget class
    
    All widgets derive from this class. On itself, this type of widget
    represents an empty space, and can be useful as a filler.
    
    Properties
    ----------
    parent (widget) : the widget that this widget is a child of.
    flex (scalar|tuple) : how flexible this widget is when used in a
        layout such as an hbox or vbox. By using a tuple, the flex can
        be set independently for the horizontal and vertical direction.
    pos (tuple) : the position of this widget in a Grid or PinBoard layout.
    min_width (scalar) : the minimum width of the widget in pixels.
    min_height (scalar) : the minimum height of the widget in pixels.
    css (str) : css styling to apply to the HTML element that represents
         this widget, e.g. ``css='background: #f00; padding: 2em;'``.
    """
    
    _counter = 0  # to produce unique id's
    
    def __init__(self, parent=None, flex=0, pos=(0, 0), 
                 min_width=0, min_height=0, css=''):
        if parent is None:
            if _default_parent:
                parent = _default_parent[-1]
            else:
                parent = get_default_app()
                #raise ValueError('Parent must be given unless it is '
                #                 'instantiated a widget context.')
        
        self._parent = None
        self._children = []
        self._set_parent(parent)
        
        self._flex = flex if isinstance(flex, tuple) else (flex, flex)
        self._pos = pos
        app = self.get_app()
        app._widget_counter += 1
        self._id = self.__class__.__name__ + str(app._widget_counter)
        
        self._min_width = min_width
        self._min_height = min_height
        self._css = css
        
        # Call function to create js_object
        self._create_js_object()
    
    def __enter__(self):
        _default_parent.append(self)
        return self
    
    def __exit__(self, type, value, traceback):
        assert self is _default_parent.pop(-1)
        if value is None:
            self.update()
    
    @property
    def parent(self):
        return self._parent
    
    def _set_parent(self, new_parent):
        old_parent = self._parent
        if old_parent is not None:
            while self in old_parent._children:
                old_parent._children.remove(self)
        if new_parent is not None:
            new_parent._children.append(self)
        self._parent = new_parent
    
    @property
    def children(self):
        return list(self._children)
    
    def update(self):
        pass
    
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
                                    pos=self._pos,
                                    hflex=self._flex[0],
                                    vflex=self._flex[1],
                                    css=self._css,
                                    min_width=self._min_width,
                                    min_height=self._min_height,
                                    **kwargs)
    
    def _create_js_object_real(self, **kwargs):
        
        eval = self.get_app()._exec
        funcname = 'create' + self.__class__.__name__
        eval('zoof.%s(%s);' % (funcname, json.dumps(kwargs)))
    
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


## Try Py -> JS decorator

from .compile import js


class Button(Widget):
    """ A Button is a widget than can be clicked on to invoke an action
    """
    
    def __init__(self, parent=None, text='Click me', **kwargs):
        self._text = text
        super().__init__(parent, **kwargs)
        
        eval = self.get_app()._exec
        # todo: arg .js -> I want eady access to info about that func
        eval('zoof.widgets.%s.%s' % (self.id, self.hello.js.jscode[5:]))
        eval('zoof.widgets.%s.%s' % (self.id, self.set_text.js.jscode[5:]))
    
    def _create_js_object_real(self, **kwargs):
        super()._create_js_object_real(text=self._text, **kwargs)
    
    def _set_text(self, text):
        self._text = text
        t = 'document.getElementById("{id}").innerHTML = "{text}"'
        self.get_app()._exec(t.format(id=self._id, text=text))
    
    @js
    def set_text(self, text):
        this.innerHTML = text  # todo: self -> this
    
    @js
    def hello(self, text):
        print('Hello world!')

_default_parent = []


class Layout(Widget):
    """ Base class for all layouts
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
        eval('zoof.get(%r).applyLayout();' % self.id)
    

# todo: spacing and margin for all layouts
# todo: combine JS code for layouts?

class HBox(Layout):
    """ An HBox is a layout widget used to align widgets horizontally
    """


class VBox(Layout):
    """ An VBox is a layout widget used to align widgets vertically
    """


class Form(Layout):
    """ A Form layout vertically stacks pairs of widgets
    
    Usually, these will be pairs of labels vs input widgets. The labels
    are on the left with flex 0, and the widgets on the right have flex
    1. The same can be achieved with a Grid, but a Form provides a more
    convienent API for this use-case.
    """


class Grid(Layout):
    """ A Grid layout aligns widgets in a grid
    
    It is more flexible than hbox and vbox, but is also slighly more
    complex to use.
    """
    
    # todo: allow different flexes per row/col
    # e.g. set_col_flex(i, flex), set_row_flex(i, flex)
    # todo: allow colspan and rowspan


class PinBoard(Layout):
    """ A PinBoard layout allows absolute positioning of its contained widgets
    
    The ``pos`` property of child widgets should be set. When larger
    than 1, the value is interpreted as pixels. If smaller than 1, it
    is interpreted as a percentage of the layout's size.
    """


class HSplit(Layout):
    """ The HSplit horizontally splits the available space in regions,
    which size can be set by the user by dragging the divider.
    """


class PHSplit(Layout):
    """ Phosphor splitter
    """


class PDockArea(Layout):
    """ Phosphor dock area
    """

class MenuBar(Widget):
    """ Phosphor menu bar
    """

class Menu(Widget):
    """ Phosphor menu
    """
    def __init__(self, parent=None, text='Blaa', **kwargs):
        self._text = text
        super().__init__(parent, **kwargs)
    
    def _create_js_object_real(self, **kwargs):
        super()._create_js_object_real(text=self._text, **kwargs)
        

class MenuItem(Widget):
    """ Phosphor menu item
    """
    def __init__(self, parent=None, text='action', **kwargs):
        self._text = text
        super().__init__(parent, **kwargs)
    
    def _create_js_object_real(self, **kwargs):
        super()._create_js_object_real(text=self._text, **kwargs)
