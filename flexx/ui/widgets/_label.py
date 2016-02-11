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
                self.label = ui.Label(flex=1, wrap=True, text='This is a label. ')
        
        class JS:
            @react.connect('but.mouse_down')
            def _add_label_text(self, down):
                if down:
                    self.label.text(self.label.text() + 'Yes it is. ')

"""

from ... import react
from ...pyscript import window
from . import Widget


class Label(Widget):
    """ Widget to show text/html.
    """
    
    CSS = """
        .flx-Label {
            border: 0px solid #454;
            /* phosphor sets this to none */
            user-select: text;
            -moz-user-select: text;
            -webkit-user-select: text;
            -ms-user-select: text;
        }"""
    
    @react.input
    def text(v=''):
        """ The text on the label.
        """
        # todo: use react.check_str() or something?
        if not isinstance(v, str):
            raise ValueError('Text input must be a string.')
        return v
    
    @react.input
    def wrap(v=False):
        """ Whether the content is allowed to be wrapped on multiple lines.
        """
        return {0: 0, 1: 1, 2: 2}.get(v, int(bool(v)))
    
    class JS:
        
        def _js_create_node(self):
            self.p = window.phosphor.createWidget('div')
        
        @react.connect('text')
        def _text_changed(self, text):
            self.node.innerHTML = text
        
        @react.connect('wrap')
        def _wrap_changed(self, wrap):
            self.node.style['word-wrap'] = ['initial', 'normal', 'break-word'][wrap]
            self.node.style['white-space'] = ['no-wrap', 'normal', 'normal'][wrap]
