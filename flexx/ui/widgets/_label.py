""" Label

.. UIExample:: 50
    from flexx import app, event, ui
    
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
    
    text = event.StringProp('', doc="""
        The text shown in the label (HTML is shown verbatim).
        """)
    
    html = event.StringProp('', doc="""
        The html shown in the label.
        
        Warning: there is a risk of introducing openings for XSS attacks
        when html is introduced that you do not control (e.g. from user input).
        """)
    
    wrap = event.IntProp(0, settable=True, doc="""
        Whether the content is allowed to be wrapped on multiple
        lines. Set to 0/False for no wrap (default), 1/True for word-wrap,
        2 for character wrap.
        """)
    
    def init(self):
        if self.text:
            self.set_text(self.text)
        elif self.html:
            self.set_html(self.html)
    
    @event.action
    def set_text(self, text):
        """ Setter for the text property.
        """
        self.node.textContent = text
        self._mutate_text(self.node.textContent)
        self._mutate_html(self.node.innerHTML)
    
    @event.action
    def set_html(self, html):
        """ Setter for the html property. Use with care.
        """
        self.node.innerHTML = html
        self._mutate_text(self.node.textContent)
        self._mutate_html(self.node.innerHTML)
    
    @event.reaction('wrap')
    def _wrap_changed(self, *events):
        wrap = self.wrap
        if wrap < 0 or wrap > 2:
            wrap = 0
        self.node.style['word-wrap'] = ['initial', 'normal', 'break-word'][wrap]
        self.node.style['white-space'] = ['nowrap', 'normal', 'normal'][wrap]
        self.check_real_size(True)
