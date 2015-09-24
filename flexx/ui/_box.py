"""
The box layout classes provide a simple mechanism to horizontally
or vertically stack child widgets.


Example:

.. UIExample:: 200
    
    from flexx import ui
    
    class Example(ui.Widget):
        def init(self):
            with ui.Box(orientation='v'):
                
                ui.Label(text='Flex 0 0 0')
                with ui.Box(flex=0):
                    self.b1 = ui.Button(text='Hola', flex=0)
                    self.b2 = ui.Button(text='Hello world', flex=0)
                    self.b3 = ui.Button(text='Foo bar', flex=0)
                
                ui.Label(text='Flex 1 0 3')
                with ui.Box(flex=0):
                    self.b1 = ui.Button(text='Hola', flex=1)
                    self.b2 = ui.Button(text='Hello world', flex=0)
                    self.b3 = ui.Button(text='Foo bar', flex=3)
                
                ui.Label(text='margin 10 (around layout)')
                with ui.Box(flex=0, margin=10):
                    self.b1 = ui.Button(text='Hola', flex=1)
                    self.b2 = ui.Button(text='Hello world', flex=1)
                    self.b3 = ui.Button(text='Foo bar', flex=1)
                
                ui.Label(text='spacing 10 (inter-widget)')
                with ui.Box(flex=0, spacing=10):
                    self.b1 = ui.Button(text='Hola', flex=1)
                    self.b2 = ui.Button(text='Hello world', flex=1)
                    self.b3 = ui.Button(text='Foo bar', flex=1)
                
                ui.Widget(flex=1)
                ui.Label(text='Note the spacer Widget above')

Interactive example:

.. UIExample:: 200
    
    from flexx import ui, react
    
    class Example(ui.Box):
        def init(self):
            self.b1 = ui.Button(text='Horizontal', flex=0)
            self.b2 = ui.Button(text='Vertical', flex=1)
            self.b3 = ui.Button(text='Horizontal reversed', flex=2)
            self.b4 = ui.Button(text='Vertical reversed', flex=3)
        
        class JS:
            
            @react.connect('b1.mouse_down')
            def _to_horizontal(self, down):
                if down: self.orientation('h')
            
            @react.connect('b2.mouse_down')
            def _to_vertical(self, down):
                if down: self.orientation('v')
            
            @react.connect('b3.mouse_down')
            def _to_horizontal_rev(self, down):
                if down: self.orientation('hr')
            
            @react.connect('b4.mouse_down')
            def _to_vertical_r(self, down):
                if down: self.orientation('vr')

"""

from .. import react
from . import Widget, Layout


class Box(Layout):
    """ Layout to organize child widgets horizontally or vertically. 
    
    This layout implements CSS flexbox. The space that each widget takes
    is determined by its minimal required size and the flex value of
    each widget. Also see ``VBox`` and ``HBox`` for shorthands.
    
    """
    
    CSS = """
    .flx-hbox, .flx-vbox, .flx-hboxr, .flx-vboxr {
        display: -webkit-flex;
        display: -ms-flexbox;  /* IE 10 */
        display: -ms-flex;     /* IE 11 */
        display: -moz-flex;
        display: flex;
        
        /* How space is divided when all flex-factors are 0: start, end, center, space-between, space-around */
        -webkit-justify-content: space-around;
        -ms-justify-content: space-around;
        -moz-justify-content: space-around;
        justify-content: space-around;
        
        /* How items are aligned in the other direction: center, stretch, baseline */
        -webkit-align-items: stretch;  
        -ms-align-items: stretch;
        -moz-align-items: stretch;
        align-items: stretch;
    }
    
    .flx-hbox {
        -webkit-flex-flow: row; -ms-flex-flow: row; -moz-flex-flow: row; flex-flow: row;
        width: 100%;
    }
    .flx-vbox {
        -webkit-flex-flow: column; -ms-flex-flow: column; -moz-flex-flow: column; flex-flow: column;
        height: 100%; width: 100%;
    }
    .flx-hboxr {
        -webkit-flex-flow: row-reverse; -ms-flex-flow: row-reverse; -moz-flex-flow: row-reverse; flex-flow: row-reverse;
        width: 100%;
    }
    .flx-vboxr {
        -webkit-flex-flow: column-reverse; -ms-flex-flow: column-reverse; -moz-flex-flow: column-reverse; flex-flow: column-reverse;
        height: 100%; width: 100%;
    }
    
    /* Make child widgets (and layouts) size correctly */
    .flx-hbox > .flx-widget, .flx-hboxr > .flx-widget {
        height: 100%;
        width: auto;
    }
    .flx-vbox > .flx-widget, .flx-vboxr > .flx-widget {
        width: 100%;
        height: auto;
    }
    """
    
    _DEFAULT_ORIENTATION = 'h'
    
    @react.input
    def margin(v=0):
        """ The empty space around the layout. """
        return float(v)
    
    @react.input
    def spacing(v=0):
        """ The space between two child elements. """
        return float(v)
    
    @react.input
    def orientation(self, v=None):
        """ The orientation of the child widgets. 'h' or 'v'. Default
        horizontal. The items can also be reversed using 'hr' and 'vr'.
        """
        if v is None:
            v = self._DEFAULT_ORIENTATION
        if isinstance(v, str):
            v = v.lower()
        v = {'horizontal': 'h', 'vertical': 'v', 0: 'h', 1: 'v'}.get(v, v)
        if v not in ('h', 'v', 'hr', 'vr'):
            raise ValueError('Unknown value for box orientation %r' % v)
        return v
    
    class JS:
    
        def _create_node(self):
            self.p = phosphor.widget.Widget()
        
        @react.connect('children.*.flex')
        def __set_flexes(*flexes):
            for widget in self.children():
                # todo: make flex 2D?
                self._applyBoxStyle(widget.node, 'flex-grow', widget.flex())
            for widget in self.children():
                widget._update_actual_size()
        
        @react.connect('spacing', 'children')
        def __spacing_changed(self, spacing, children):
            if children.length:
                children[0].node.style['margin-left'] = '0px'
                for child in children[1:]:
                    child.node.style['margin-left'] = spacing + 'px'
                for widget in self.children():
                    widget._update_actual_size()
        
        @react.connect('margin')
        def __margin_changed(self, margin):
            self.node.style['padding'] = margin + 'px'
            for widget in self.children():
                widget._update_actual_size()
        
        @react.connect('orientation')
        def __orientation_changed(self, orientation):
            for name in ('hbox', 'vbox', 'hboxr', 'vboxr'):
                self.node.classList.remove('flx-'+name)
            if orientation == 0 or orientation == 'h':
                self.node.classList.add('flx-hbox')
            elif orientation == 1 or orientation == 'v':
                self.node.classList.add('flx-vbox')
            elif orientation == 'hr':
                self.node.classList.add('flx-hboxr')
            elif orientation == 'vr':
                self.node.classList.add('flx-vboxr')
            else:
                raise ValueError('Invalid box orientation: ' + orientation)


class HBox(Box):
    """ Box layout with default horizontal layout.
    """
    _DEFAULT_ORIENTATION = 'h'


class VBox(Box):
    """ LBox layout with default vertical layout.
    """
    _DEFAULT_ORIENTATION = 'v'
