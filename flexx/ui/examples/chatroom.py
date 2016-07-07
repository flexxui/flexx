"""
Simple chat web app in less than 80 lines.

This app might be running at the demo server: http://flexx1.zoof.io
"""

from flexx import app, ui, event


class Relay(event.HasEvents):
    """ Global object to relay messages to all participants.
    """
    @event.emitter
    def new_message(self, msg):
        return dict(msg=msg + '<br />')


class MessageBox(ui.Label):
    CSS = """
    .flx-MessageBox {
        overflow-y:scroll;
        background: #e8e8e8;
        border: 1px solid #444;
        margin: 3px;
    }
    """


class ChatRoom(ui.Widget):
    """ Despite the name, this represents one connection to the chat room.
    """
    
    def init(self):
        with ui.HBox():
            ui.Widget(flex=1)
            with ui.VBox():
                self.name = ui.LineEdit(placeholder_text='your name')
                self.people = ui.Label(flex=1, base_size=(250, 0))
            with ui.VBox():
                self.messages = MessageBox(flex=1)
                with ui.HBox():
                    self.message = ui.LineEdit(flex=1, placeholder_text='enter message')
                    self.ok = ui.Button(text='Send')
            ui.Widget(flex=1)
        
        # Pipe messages send by the relay into this app
        relay.connect(self._push_info, 'new_message:' + self.id)
        
        self._update_participants()
    
    def _push_info(self, *events):
        if self.session.status:
            for ev in events:
                self.emit('new_message', ev)
    
    def _update_participants(self):
        if not self.session.status:
            relay.disconnect('new_message:' + self.id)
            return  # and dont't invoke a new call
        proxies = app.manager.get_connections(self.__class__.__name__)
        names = [p.app.name.text for p in proxies]
        del proxies
        text = '<br />%i persons in this chat:<br /><br />' % len(names)
        text += '<br />'.join([name or 'anonymous' for name in sorted(names)])
        self.people.text = text
        app.call_later(3, self._update_participants)
    
    @event.connect('ok.mouse_down', 'message.submit')
    def _send_message(self, *events):
        text = self.message.text
        if text:
            name = self.name.text or 'anonymous'
            relay.new_message('<i>%s</i>: %s' % (name, text))
            self.message.text = ''
    
    class JS:
        
        @event.connect('new_message')
        def _update_total_text(self, *events):
            self.messages.text += ''.join([ev.msg for ev in events])


# Create global relay
relay = Relay()

if __name__ == '__main__':
    app.serve(ChatRoom)
    # m = app.launch(ChatRoom)  # for use during development
    app.start()
