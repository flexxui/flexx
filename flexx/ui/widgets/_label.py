""" Label

.. UIExample:: 50
    from flexx import app, ui, event
    
    class Example(ui.Widget):
    
        def init(self):
            with ui.HBox():
                self.but = ui.Button(text='Push me')
                self.label = ui.Label(flex=1, wrap=True, text='This is a label. ')
    
        @event.reaction('but.mouse_down')
        def _add_label_text(self, *events):
            self.label.set_text(self.label.text + 'Yes it is. ')

"""

from ... import event
from . import Widget


class Label(Widget):
    """ Widget to show text/html.
    """
    
    CSS = """
        .flx-Label {
            border: 0px solid #454;
            user-select: text;
            -moz-user-select: text;
            -webkit-user-select: text;
            -ms-user-select: text;
        }"""
    
    text = event.StringProp('', settable=True, doc="""
        The text on the label.
        """)
    
    wrap = event.IntProp(0, doc="""
        Whether the content is allowed to be wrapped on multiple
        lines. Set to 0/False for no wrap, 1/True for word-wrap, 2 for
        character wrap.
        """)

    @event.action
    def set_wrap(self, wrap):
        """ Set wrap"""
        wrap = int(wrap)
        if wrap < 0 or wrap > 2:
            wrap = 0
        self._mutate_wrap(wrap)
    
    @event.reaction('text')
    def _text_changed(self, *events):
        self.node.innerHTML = self.text
        self.check_real_size(True)
    
    @event.reaction('wrap')
    def _wrap_changed(self, *events):
        wrap = self.wrap
        self.node.style['word-wrap'] = ['initial', 'normal', 'break-word'][wrap]
        self.node.style['white-space'] = ['nowrap', 'normal', 'normal'][wrap]
        self.check_real_size(True)
