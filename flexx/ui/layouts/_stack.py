"""
Example:

.. UIExample:: 200
    
    from flexx import ui, event

    class Example(app.PyComponent):
        
        def init(self):
            with ui.HBox():
                with ui.VBox():
                    self.buta = ui.Button(text='red')
                    self.butb = ui.Button(text='green')
                    self.butc = ui.Button(text='blue')
                    ui.Widget(flex=1)  # space filler
                with ui.StackLayout(flex=1) as self.stack:
                    self.buta.w = ui.Widget(style='background:#a00;')
                    self.butb.w = ui.Widget(style='background:#0a0;')
                    self.butc.w = ui.Widget(style='background:#00a;')
    
        @event.reaction('buta.mouse_down', 'butb.mouse_down', 'butc.mouse_down')
        def _stacked_current(self, *events):
            button = events[-1].source
            self.stack.set_current(button.w)
"""

from ... import event
from ...pyscript import RawJS
from . import Widget, Layout


class StackLayout(Layout):
    """ A panel which shows only one of its children at a time.
    """
    
    CSS = """
        .flx-StackLayout > .flx-Widget {
            position: absolute;
            left: 0;
            top: 0;
            right: 0;
            bottom: 0;
            width: 100%;
            height: 100%;
        }
        .flx-StackLayout > .flx-Widget:not(.flx-current) {
            display: none;
        }
    """
    
    current = event.ComponentProp(doc="""
            The currently shown widget (or None).
            """)
    
    @event.action
    def set_current(self, current):
        """ Setter for current widget. Can also set using an integer index.
        """
        if isinstance(current, (float, int)):
            current = self.children[int(current)]
        self._mutate_current(current)
    
    @event.reaction
    def __set_current_widget(self):
        current = self.current
        children = self.children
        
        if len(children) == 0:
            if current is not None:
                self.set_current(None)
        else:
            if current is None:
                current = children[0]
                self.set_current(current)
        
            for widget in self.children:
                if widget is current:
                    widget.outernode.classList.add('flx-current')
                else:
                    widget.outernode.classList.remove('flx-current')
