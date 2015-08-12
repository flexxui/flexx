""" Button widgets.
"""

from .. import react
from . import Widget



class Button(Widget):
    """ A simple push button.
    
    Example:
    
    .. UIExample:: 100
        
        from flexx import ui
        
        class App(ui.App):
            def init(self):
                self.b1 = ui.Button(text='Push me!')
    
    """
    
    CSS = """
    .flx-button-xxx {
        background: #fee;
    }
    """
    
    @react.input
    def text(v=''):
        """ The text on the button.
        """
        # todo: use react.check_str() or something?
        if not isinstance(v, str):
            raise ValueError('Text input must be a string.')
        return v
    
    class JS:
        
        def _create_node(self):
            this.node = document.createElement('button')
            #this._proxy_event(this.node, 'click')
            
            # testing ...
            #self.connect_event('click', (self, 'ontheclick'))
        
        @react.connect('text')
        def _text_changed(self, text):
            this.node.innerHTML = text
    
        @react.source
        def mouse_down(v=False):
            return bool(v)
