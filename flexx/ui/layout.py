""" Layout widgets
"""

from ..pyscript import js
from ..properties import Prop, Instance, Str, Tuple, Float

from .widget import Widget


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
    
    @js
    def _js_init(self):
        this.node = document.createElement('div')
        #this.node.className = self.cssClassName
        flexx.get('body').appendChild(this.node);
    
    @js
    def _js_set_child(self, el):
        self._applyBoxStyle(el.node, 'flex-grow', el.flex)
        self._applyBoxStyle(el.node, 'align-items', 'center')  # flex-start, flex-end, center, baseline, stretch
        self._applyBoxStyle(el.node, 'justify-content', 'space-around')  # flex-start, flex-end, center, space-between, space-around
       
        super()._set_child(el)


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
