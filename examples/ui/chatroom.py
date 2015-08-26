"""
Simple chat web app in less than 80 lines.
"""

from flexx import app, ui, react

nsamples = 16


@react.input
def message_relay(msg):
    """ One global signal to relay messages to all participants.
    """
    return msg + '<br />'


class MessageBox(ui.Label):
    CSS = """
    .flx-messagebox {
        overflow-y:scroll;
        background: #e8e8e8;
        border: 1px solid #444;
        margin: 3px;
    }
    """


@app.serve
class ChatRoom(ui.Widget):
    """ Despite the name, this represents one connection to the chat room.
    """
    
    def init(self):
        with ui.HBox():
            ui.Widget(flex=1)
            with ui.VBox():
                self.name = ui.LineEdit(placeholder_text='your name')
                self.people = ui.Label(flex=1, size=(250, 0))
            with ui.VBox():
                self.messages = MessageBox(flex=1)
                with ui.HBox():
                    self.message = ui.LineEdit(flex=1, placeholder_text='enter message')
                    self.ok = ui.Button(text='Send')
            ui.Widget(flex=1)
        
        self._update_participants()
    
    def _update_participants(self):
        proxies = app.manager.get_connections(self.__class__.__name__)
        names = [p.app.name.text() for p in proxies]
        text = '<br />%i persons in this chat:<br /><br />' % len(names)
        text += '<br />'.join([name or 'anonymous' for name in sorted(names)])
        self.people.text(text)
        app.call_later(3, self._update_participants)
    
    @react.connect('ok.mouse_down', 'message.submit')
    def _send_message(self, down, submit):
        text = self.message.text()
        if text:
            name = self.name.text() or 'anonymous'
            message_relay('<i>%s</i>: %s' % (name, text))
            self.message.text('')
    
    @react.connect('message_relay')
    def new_text(self, text):
        return text  # proxy to pass total_text to JS
    
    class JS:
        
        @react.connect('new_text')
        def _update_total_text(self, text):
            self.messages.text(self.messages.text() + text)


if __name__ == '__main__':
    #m = app.launch(ChatRoom)  # for use during development
    app.start()
