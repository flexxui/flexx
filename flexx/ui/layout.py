""" Layout widgets
"""

from ..pyscript import js
from ..properties import Prop, Instance, Str, Tuple, Float, Int

from .widget import Widget


# todo: rename "zf-" prefix to "xx" or something


class Layout(Widget):
    CSS = """
    
    html {
        /* set height, so body can have height, and the first layout too */
        height: 100%;  
    }
    
    body {
        /* Set height so the first layout can fill whole window */
        height: 100%;
        margin: 0px;
    }
    
    .zf-layout {
        width: 100%;
        height: 100%;
        margin: 0px;
        padding: 0px;
        border-spacing: 0px;
        border: 0px;
    }
    
    """
    
    @js
    def _js_applyBoxStyle(self, e, sty, value):
        for prefix in ['-webkit-', '-ms-', '-moz-', '']:
            e.style[prefix + sty] = value



class Box(Layout):
    """ Abstract class for HBox and VBox
    """
    
    CSS = """
    .zf-hbox, .zf-vbox {
        display: -webkit-flex;
        display: -ms-flexbox;  /* IE 10 */
        display: -ms-flex;     /* IE 11 */
        display: -moz-flex;
        display: flex;
        
        justify-content: stretch;  /* start, end, center, space-between, space-around */
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
    
    margin = Float()
    spacing = Float()
    
    @js
    def _js_create_node(self):
        this.node = document.createElement('div')
    
    @js
    def _js_add_child(self, widget):
        self._applyBoxStyle(widget.node, 'flex-grow', widget.flex)
        #if widget.flex > 0:  widget.applyBoxStyle(el, 'flex-basis', 0)
        self._spacing_changed('spacing', self.spacing, self.spacing)
        super()._add_child(widget)
    
    @js
    def _js_remove_child(self, widget):
        self._spacing_changed('spacing', self.spacing, self.spacing)
        super()._remove_child(widget)
    
    @js
    def _js_spacing_changed(self, name, old, spacing):
        if self.children.length:
            self.children[0].node.style['margin-left'] = '0px'
            for child in self.children[1:]:
                child.node.style['margin-left'] = spacing + 'px'
    
    @js
    def _js_margin_changed(self, name, old, margin):
        self.node.style['padding'] = margin + 'px'


class HBox(Box):
    """ Layout widget to align elements horizontally.
    """
    
    CSS = """
    .zf-hbox {
        -webkit-flex-flow: row;
        -ms-flex-flow: row;
        -moz-flex-flow: row;
        flex-flow: row;
        width: 100%;
        /*border: 1px dashed #44e;*/
    }
    """
    
    @js
    def _js_init(self):
        super()._init()
        # align-items: flex-start, flex-end, center, baseline, stretch
        self._applyBoxStyle(self.node, 'align-items', 'center')
        #justify-content: flex-start, flex-end, center, space-between, space-around
        self._applyBoxStyle(self.node, 'justify-content', 'space-around')
        

class VBox(Box):
    """ Layout widget to align elements vertically.
    """
    
    CSS = """
    .zf-vbox {
        -webkit-flex-flow: column;
        -ms-flex-flow: column;
        -moz-flex-flow: column;
        flex-flow: column;
        height: 100%;
        width: 100%;
        /*border: 1px dashed #e44;*/
    }
    """
    
    @js
    def _js_init(self):
        super()._init()
        self._applyBoxStyle(self.node, 'align-items', 'stretch')
        self._applyBoxStyle(self.node, 'justify-content', 'space-around')
