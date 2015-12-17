"""
The box layout classes provide a simple mechanism to horizontally
or vertically stack child widgets. There is a BoxLayout for laying out
leaf content taking into account natural size, and a BoxPanel for
higher-level layout.


Example for BoxLayout:

.. UIExample:: 250
    
    from flexx import ui
    
    class Example(ui.Widget):
        def init(self):
            with ui.BoxLayout(orientation='v'):
                
                ui.Label(text='Flex 0 0 0')
                with ui.HBox(flex=0):
                    self.b1 = ui.Button(text='Hola', flex=0)
                    self.b2 = ui.Button(text='Hello world', flex=0)
                    self.b3 = ui.Button(text='Foo bar', flex=0)
                
                ui.Label(text='Flex 1 0 3')
                with ui.HBox(flex=0):
                    self.b1 = ui.Button(text='Hola', flex=1)
                    self.b2 = ui.Button(text='Hello world', flex=0)
                    self.b3 = ui.Button(text='Foo bar', flex=3)
                
                ui.Label(text='padding 10 (around layout)')
                with ui.HBox(flex=0, padding=10):
                    self.b1 = ui.Button(text='Hola', flex=1)
                    self.b2 = ui.Button(text='Hello world', flex=1)
                    self.b3 = ui.Button(text='Foo bar', flex=1)
                
                ui.Label(text='spacing 10 (inter-widget)')
                with ui.HBox(flex=0, spacing=10):
                    self.b1 = ui.Button(text='Hola', flex=1)
                    self.b2 = ui.Button(text='Hello world', flex=1)
                    self.b3 = ui.Button(text='Foo bar', flex=1)
                
                ui.Widget(flex=1)
                ui.Label(text='Note the spacer Widget above')


A similar example using a BoxPanel:

.. UIExample:: 250
    
    from flexx import ui
    
    class Example(ui.Widget):
        def init(self):
            with ui.BoxPanel(orientation='v'):
                
                ui.Label(text='Flex 0 0 0', style='')
                with ui.BoxPanel(flex=0):
                    self.b1 = ui.Button(text='Hola', flex=0)
                    self.b2 = ui.Button(text='Hello world', flex=0)
                    self.b3 = ui.Button(text='Foo bar', flex=0)
                
                ui.Label(text='Flex 1 0 3')
                with ui.BoxPanel(flex=0):
                    self.b1 = ui.Button(text='Hola', flex=1)
                    self.b2 = ui.Button(text='Hello world', flex=0)
                    self.b3 = ui.Button(text='Foo bar', flex=3)
                
                ui.Label(text='spacing 10 (inter-widget)')
                with ui.BoxPanel(flex=0, spacing=20):
                    self.b1 = ui.Button(text='Hola', flex=1)
                    self.b2 = ui.Button(text='Hello world', flex=1)
                    self.b3 = ui.Button(text='Foo bar', flex=1)
                
                ui.Widget(flex=1)


Interactive example:

.. UIExample:: 200
    
    from flexx import ui, react
    
    class Example(ui.HBox):
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

from ... import react
from ...pyscript import window
from . import Layout


class BaseBoxLayout(Layout):
    """ Base class for BoxLayout and BoxPanel.
    """
    
    @react.input
    def spacing(v=5):
        """ The space between two child elements (in pixels)"""
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


class BoxLayout(BaseBoxLayout):
    """ Layout to distribute space for widgets horizontally or vertically. 
    
    This layout implements CSS flexbox. The space that each widget takes
    is determined by its minimal required size and the flex value of
    each widget. Also see ``VBox`` and ``HBox`` for shorthands.
    """
    
    _DEFAULT_ORIENTATION = 'h'
    
    CSS = """
    .flx-hbox, .flx-vbox, .flx-hboxr, .flx-vboxr {
        display: -webkit-flex;
        display: -ms-flexbox;  /* IE 10 */
        display: -ms-flex;     /* IE 11 */
        display: -moz-flex;
        display: flex;
        
        /* How space is divided when all flex-factors are 0:
           start, end, center, space-between, space-around */
        -webkit-justify-content: space-around;
        -ms-justify-content: space-around;
        -moz-justify-content: space-around;
        justify-content: space-around;
        
        /* How items are aligned in the other direction:
           center, stretch, baseline */
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
        -webkit-flex-flow: column;
        -ms-flex-flow: column;
        -moz-flex-flow: column;
        flex-flow: column;
        height: 100%; width: 100%;
    }
    .flx-hboxr {
        -webkit-flex-flow: row-reverse;
        -ms-flex-flow: row-reverse;
        -moz-flex-flow: row-reverse;
        flex-flow: row-reverse;
        width: 100%;
    }
    .flx-vboxr {
        -webkit-flex-flow: column-reverse;
        -ms-flex-flow: column-reverse;
        -moz-flex-flow: column-reverse;
        flex-flow: column-reverse;
        height: 100%; width: 100%;
    }
    
    /* Make child widgets (and layouts) size correctly */
    .flx-hbox > .flx-Widget, .flx-hboxr > .flx-Widget {
        height: auto;
        width: auto;
    }
    .flx-vbox > .flx-Widget, .flx-vboxr > .flx-Widget {
        width: auto;
        height: auto;
    }
    
    /* If a boxLayout is in a compound widget, we need to make that widget
       a flex container (done with JS in Widget class), and scale here */
    .flx-Widget > .flx-BoxLayout {
        flex-grow: 1;
    }
    """
    
    @react.input
    def padding(v=1):
        """ The empty space around the layout (in pixels). """
        return float(v)
    
    class JS:
    
        def _create_node(self):
            self.p = window.phosphor.widget.Panel()
        
        @react.connect('orientation', 'children.*.flex')
        def __set_flexes(self, ori, *flexes):
            i = 0 if ori in (0, 'h', 'hr') else 1
            for widget in self.children():
                self._applyBoxStyle(widget.node, 'flex-grow', widget.flex()[i])
            for widget in self.children():
                widget._check_real_size()
        
        @react.connect('spacing', 'orientation', 'children')
        def __spacing_changed(self, spacing, ori, children):
            # Reset
            for child in self.children.value:
                child.node.style['margin-top'] = ''
                child.node.style['margin-left'] = ''
            if self.children.last_value:
                for child in self.children.last_value:
                    child.node.style['margin-top'] = ''
                    child.node.style['margin-left'] = ''
            # Set
            margin = 'margin-top' if ori in (1, 'v', 'vr') else 'margin-left'
            if children.length:
                if ori in ('vr', 'hr'):
                    children[-1].node.style[margin] = '0px'
                    for child in children[:-1]:
                        child.node.style[margin] = spacing + 'px'
                else:
                    children[0].node.style[margin] = '0px'
                    for child in children[1:]:
                        child.node.style[margin] = spacing + 'px'
            for widget in self.children():
                widget._check_real_size()
        
        @react.connect('padding')
        def __padding_changed(self, margin):
            self.node.style['padding'] = margin + 'px'
            for widget in self.children():
                widget._check_real_size()
        
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
            for widget in self.children():
                widget._check_real_size()
        
        def _applyBoxStyle(self, e, sty, value):
            for prefix in ['-webkit-', '-ms-', '-moz-', '']:
                e.style[prefix + sty] = value


class HBox(BoxLayout):
    """ BoxLayout with default horizontal layout.
    """
    _DEFAULT_ORIENTATION = 'h'


class VBox(BoxLayout):
    """ BoxLayout with default vertical layout.
    """
    _DEFAULT_ORIENTATION = 'v'


class BoxPanel(BaseBoxLayout):
    """ Layout to distribute space for widgets horizontally or vertically.
    
    The BoxPanel differs from the Box layout in that the natural size
    of widgets is *not* taken into account. Only the minimum, maximum
    and base size are used to do the layout. It is therefore more
    suited for high-level layout.
    """
    
    _DEFAULT_ORIENTATION = 'h'
    
    class JS:
        
        def _create_node(self):
            self.p = window.phosphor.boxpanel.BoxPanel()
        
        @react.connect('orientation', 'children.*.flex')
        def __set_flexes(self, ori, *flexes):
            i = 0 if ori in (0, 'h', 'hr') else 1
            for widget in self.children():
                window.phosphor.boxpanel.BoxPanel.setStretch(widget.p, widget.flex()[i])
                window.phosphor.boxpanel.BoxPanel.setSizeBasis(widget.p, 100)
        
        @react.connect('spacing')
        def __spacing_changed(self, spacing):
            self.p.spacing = spacing
        
        @react.connect('orientation')
        def __orientation_changed(self, orientation):
            if orientation == 0 or orientation == 'h':
                self.p.direction = window.phosphor.boxpanel.BoxPanel.LeftToRight
            elif orientation == 1 or orientation == 'v':
                self.p.direction = window.phosphor.boxpanel.BoxPanel.TopToBottom
            elif orientation == 'hr':
                self.p.direction = window.phosphor.boxpanel.BoxPanel.RightToLeft
            elif orientation == 'vr':
                self.p.direction = window.phosphor.boxpanel.BoxPanel.BottomToTop
            else:
                raise ValueError('Invalid boxpanel orientation: ' + orientation)
