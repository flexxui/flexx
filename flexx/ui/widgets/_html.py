"""

Simple example:

.. UIExample:: 75
    
    from flexx import app, ui
    
    class Example(ui.Widget):
        
        def init(self):
        
            with ui.html.UL():
                ui.html.LI(text='foo')
                ui.html.LI(text='bar')


.. UIExample:: 150
    
    from flexx import app, ui, event
    
    class Example(ui.Widget):
        
        def init(self):
        
            with ui.html.UL():
                ui.html.LI(text='foo')
                ui.html.LI(text='bar')
                with ui.html.LI():
                    with ui.html.I():
                        self.now = ui.html.Span(text='0')
            self.but = ui.html.Button(text='press me')
        
        class JS:
            
            @event.connect('but.mouse_down')
            def on_click(self, *events):
                self.now.text = window.Date.now()

"""


from ... import event
from . import Widget


class Div(Widget):
    """
    This class is the base class for "HTML widgets". These provides a
    lower-level way of working with HTML content that can feel more
    natural to users with a background in web development.
    
    Via the ``flexx.ui.html`` factory object, it is possible to create *any*
    type of DOM element. E.g. ``ui.html.Table()`` creates an table and
    ``ui.html.b(text='foo')`` creates a piece of bold text.
    
    Since this class inherits from ``Widget``, all base widget functionality
    (e.g. mouse events) work as expected. However, the specific functionality
    of each element (e.g. ``src`` for img elements) must be used in the
    "JavaScript way".
    
    In contrast to regular Flexx widgets, the css class name of the node only
    consists of the name(s) provided via the ``css_class`` property.
    
    Also see :ref:`this example <classic_web_dev.py>`.
    """
    
    class Both:
        
        @event.prop
        def text(self, v=''):
            """ The inner HTML for this element.
            """
            return str(v)
    
    class JS:
        
        def __init__(self, *args):
            super().__init__(*args)
            self.node.className = ''
        
        def _init_phosphor_and_node(self):
            self.phosphor = self._create_phosphor_widget(self._class_name.lower())
            self.node = self.phosphor.node
        
        @event.connect('text')
        def __on_inner_html(self, *events):
            self.node.innerHTML = events[-1].new_value
        
        def _add_child(self, widget):
            self.node.appendChild(widget.node)


class HTMLElementFactory:
    """
    This object can be used to generate a Flexx Widget class for any
    HTML element that you'd like. These Widget classes inherit from ``Div``.
    """
    
    def __getattr__(self, name):
        name = name.lower()
        cache = globals()
        if name.startswith('_'):
            return super().__getattr__(name)
        if name not in cache:
            # Create new class, put it in this module so that JSModule can find it
            cls = type(name, (Div,), {})
            cls.__module__ = cls.__jsmodule__ = __name__
            cache[name] = cls
        return cache[name]


html = HTMLElementFactory()
