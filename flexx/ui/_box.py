"""
The box layout classes provide a simple mechanism to horizontally
or vertically stack child widgets.


Example:

.. UIExample:: 200
    
    from flexx import ui
    
    class Example(ui.Widget):
        def init(self):
            with ui.VBox():
                
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
                
                ui.Label(text='margin 10 (around layout)')
                with ui.HBox(flex=0, margin=10):
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
"""

from .. import react
from . import Widget, Layout

class Box(Layout):
    """ Abstract class for HBox and VBox.
    
    Child widgets are tiled either horizontally or vertically. The space
    that each widget takes is determined by its minimal required size
    and the flex value of each widget.
    
    """
    
    CSS = """
    .flx-hbox, .flx-vbox {
        display: -webkit-flex;
        display: -ms-flexbox;  /* IE 10 */
        display: -ms-flex;     /* IE 11 */
        display: -moz-flex;
        display: flex;
        
        justify-content: stretch;  /* start, end, center, space-between, space-around */
        align-items: stretch;
        align-content: stretch;
    }
    
    /*
    .box-align-center { -webkit-align-items: center; -ms-align-items: center; -moz-align-items: center; align-items: center; }
    .box-align-center { -webkit-align-items: center; -ms-align-items: center; -moz-align-items: center; align-items: center; }
    */
    
    /* Make child widgets (and layouts) size correctly */
    .flx-hbox > .flx-widget {
        height: 100%;
        width: auto;
    }
    .flx-vbox > .flx-widget {
        width: 100%;
        height: auto;
    }
    """
    
    @react.input
    def margin(v=0):
        """ The empty space around the layout. """
        return float(v)
    
    @react.input
    def spacing(v=0):
        """ The space between two child elements. """
        return float(v)
    
    class JS:
    
        def _create_node(self):
            self.p = phosphor.widget.Widget()
        
        @react.connect('children.*.flex')
        def _set_flexes(*flexes):
            for widget in self.children():
                # todo: make flex 2D?
                self._applyBoxStyle(widget.node, 'flex-grow', widget.flex())
            for widget in self.children():
                widget._update_actual_size()
        
        @react.connect('spacing', 'children')
        def _spacing_changed(self, spacing, children):
            if children.length:
                children[0].node.style['margin-left'] = '0px'
                for child in children[1:]:
                    child.node.style['margin-left'] = spacing + 'px'
                for widget in self.children():
                    widget._update_actual_size()
        @react.connect('margin')
        def _margin_changed(self, margin):
            self.node.style['padding'] = margin + 'px'
            for widget in self.children():
                widget._update_actual_size()
                

class HBox(Box):
    """ Layout widget to distribute elements horizontally.
    See Box for more info.
    """
    
    CSS = """
    .flx-hbox {
        -webkit-flex-flow: row;
        -ms-flex-flow: row;
        -moz-flex-flow: row;
        flex-flow: row;
        width: 100%;
        /*border: 1px dashed #44e;*/
    }
    """
    
    class JS:
        def _init(self):
            super()._init()
            # align-items: flex-start, flex-end, center, baseline, stretch
            self._applyBoxStyle(self.node, 'align-items', 'center')
            #justify-content: flex-start, flex-end, center, space-between, space-around
            self._applyBoxStyle(self.node, 'justify-content', 'space-around')


class VBox(Box):
    """ Layout widget to distribute elements vertically.
    See Box for more info.
    """
    
    CSS = """
    .flx-vbox {
        -webkit-flex-flow: column;
        -ms-flex-flow: column;
        -moz-flex-flow: column;
        flex-flow: column;
        height: 100%;
        width: 100%;
        /*border: 1px dashed #e44;*/
    }
    """
    
    class JS:
        def _init(self):
            super()._init()
            self._applyBoxStyle(self.node, 'align-items', 'stretch')
            self._applyBoxStyle(self.node, 'justify-content', 'space-around')
