"""

Simple example:

.. UIExample:: 50
    
    b = ui.Button(text="Push me")


Example with interaction:

.. UIExample:: 50
    
    from flexx import app, ui, react
    
    class Example(ui.Widget):
    
        def init(self):
            self.b1 = ui.Button(text="I've been clicked 0 times")
        
        class JS:
        
            @react.connect('b1.mouse_down')
            def _on_mouse_down(down):
                self._click_count = self._click_count or 0
                if down:
                    self._click_count += 1
                    self.b1.text("I've been clicked %i times" % self._click_count)

"""

from ... import react
from ...pyscript import window
from . import Widget



class Button(Widget):
    """ A simple push button.
    """
    
    CSS = """
    
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
            self.p = window.phosphor.createWidget('button')
            node = self.p.node
            that = self
            node.addEventListener('mousedown', lambda ev: that.mouse_down._set(1), 0)
            node.addEventListener('mouseup', lambda ev: that.mouse_down._set(0), 0)
        
        @react.connect('text')
        def _text_changed(self, text):
            self.node.innerHTML = text
    
        @react.source
        def mouse_down(v=False):
            """ True when the mouse is currently pressed down.
            """
            return bool(v)
