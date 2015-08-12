"""

Simple example:

.. UIExample:: 50
    
    label = ui.Label(text='This is a label')

Interactive example:

.. UIExample:: 50
    from flexx import app, ui, react
    
    class Example(ui.Widget):
    
        def init(self):
            with ui.HBox():
                self.but = ui.Button(text='Push me')
                self.label = ui.Label(flex=1, text='This is a label. ')
        
        class JS:
            @react.connect('but.mouse_down')
            def _add_label_text(self, down):
                if down:
                    self.label.text(self.label.text() + 'Yes it is. ')

"""

from .. import react
from . import Widget


class Label(Widget):
    """ Widget to show text/html.
    """
    
    CSS = ".flx-label { border: 0px solid #454; }"

    @react.input
    def text(v=''):
        """ The text on the label.
        """
        # todo: use react.check_str() or something?
        if not isinstance(v, str):
            raise ValueError('Text input must be a string.')
        return v
    
    class JS:
        
        def _js_create_node(self):
            # todo: allow setting a placeholder DOM element, or any widget parent
            this.node = document.createElement('div')
            #this.node.className = this.cssClassName
            flexx.get('body').appendChild(this.node);
            # this.node.innerHTML = 'a label'
            # super()._init()
        
        @react.connect('text')
        def _text_changed(self, text):
            this.node.innerHTML = text
