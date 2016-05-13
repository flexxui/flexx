"""

Simple example:

.. UIExample:: 50
    
    b = ui.Button(text="Push me")


Example with interaction:

.. UIExample:: 50
    
    from flexx import app, ui, event
    
    class Example(ui.Widget):
    
        def init(self):
            self.b1 = ui.Button(text="I've been clicked 0 times")
        
        class JS:
        
            @event.connect('b1.mouse_click')
            def _on_mouse_click(self, *events):
                self._click_count = self._click_count or 0
                self._click_count += len(events)
                self.b1.text = "I've been clicked %i times" % self._click_count

"""

from ... import event
from ...pyscript import window
from . import Widget



class Button(Widget):
    """ A simple push button.
    """
    
    CSS = """
    
    """
    
    @event.prop(both=True)
    def text(self, v=''):
        """ The text on the button.
        """
        return str(v)
    
    class JS:
        
        def _init_phosphor_and_node(self):
            self.phosphor = window.phosphor.createWidget('button')
            self.node = self.phosphor.node
            self.node.addEventListener('click', self.mouse_click, 0)
        
        @event.emitter
        def mouse_click(self, e):
            """ Event emitted when the mouse is clicked.
            
            See mouse_down() for a description of the event object.
            """
            return self._create_mouse_event(e)
        
        @event.connect('text')
        def __text_changed(self, *events):
            self.node.innerHTML = events[-1].new_value
