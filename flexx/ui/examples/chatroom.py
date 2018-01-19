"""
Simple chat web app inabout 80 lines.

This app might be running at the demo server: http://flexx1.zoof.io
"""

from flexx import app, event, ui
import asyncio


class Relay(event.Component):
    """ Global object to relay messages to all participants.
    """
    
    @event.emitter
    def create_message(self, msg):
        return dict(message=msg)

# Create global relay
relay = Relay()


class MessageBox(ui.Label):
    
    CSS = """
    .flx-MessageBox {
        overflow-y:scroll;
        background: #e8e8e8;
        border: 1px solid #444;
        margin: 3px;
    }
    """
    
    @event.action
    def add_message(self, msg):
        self.set_text(self.text + msg + '<br />')


class ChatRoom(app.PyComponent):
    """ This represents one connection to the chat room.
    """
    
    def init(self):
        with ui.HBox(title='Flexx chatroom demo'):
            ui.Widget(flex=1)
            with ui.VBox():
                self.name_edit = ui.LineEdit(placeholder_text='your name')
                self.people_label = ui.Label(flex=1, style='min-width: 250px')
            with ui.VBox(style='min-width: 450px'):
                self.messages = MessageBox(flex=1)
                with ui.HBox():
                    self.msg_edit = ui.LineEdit(flex=1,
                                                placeholder_text='enter message')
                    self.ok = ui.Button(text='Send')
            ui.Widget(flex=1)
        
        self._update_participants()
    
    @event.reaction('ok.mouse_down', 'msg_edit.submit')
    def _send_message(self, *events):
        text = self.msg_edit.text
        if text:
            name = self.name.text or 'anonymous'
            relay.create_message('<i>%s</i>: %s' % (name, text))
            self.msg_edit.set_text('')
    
    @relay.reaction('create_message')  # note that we connect to relay
    def _push_info(self, *events):
        for ev in events:
            self.messages.add_message(ev.message)
    
    def _update_participants(self):
        # Query the app manager to see who's in the room
        if not self.session.status:
            return  # and dont't invoke a new call
        sessions = app.manager.get_connections(self.session.app_name)
        names = [s.app.name_edit.text for s in sessions]
        del sessions
        text = '<br />%i persons in this chat:<br /><br />' % len(names)
        text += '<br />'.join([name or 'anonymous' for name in sorted(names)])
        self.people_label.set_text(text)
        asyncio.get_event_loop().call_later(3, self._update_participants)


if __name__ == '__main__':
    a = app.App(ChatRoom)
    a.serve()
    # a.launch()  # for use during development
    app.start()
