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
        
            @event.connect('b1.mouse_down')
            def _on_mouse_down(self, *events):
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
    
    @event.prop
    def text(self, v=''):
        """ The text on the button.
        """
        # todo: use event.check_str() or something?
        if not isinstance(v, str):
            raise ValueError('Text property must be a string.')
        return v
    
    class JS:
        
        def init(self):
            self.p = window.phosphor.createWidget('button')
            node = self.p.node
            node.addEventListener('mousedown', self.mouse_down.bind(this), 0)
            node.addEventListener('mouseup', self.mouse_up, 0)
        
        @event.connect('text')
        def __text_changed(self, *events):
            self.node.innerHTML = events[-1].new_value
        
        # todo: docs on the mouse event
        @event.emitter
        def mouse_down(self, e):
            """ Event emitted when the mouse is pressed down.
            """
            return self._create_mouse_event(e)
        
        @event.emitter
        def mouse_up(self, e):
            """ Event emitted when the mouse is pressed up.
            """
            return self._create_mouse_event(e)
        
        def _create_mouse_event(self, e):
            # todo: which vs button? see also lineedit
            modifiers = [n for n in ('alt', 'shift', 'ctrl', 'meta') if e[n]]
            return dict(x=e.clientX, y=e.clientY,
                        pageX=e.pageX, pageY=e.pageY,
                        button=e.button+1, buttons=[b+1 for b in e.buttons],
                        modifiers=modifiers,
                        )

