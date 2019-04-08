"""
Simple chat web app inabout 80 lines.

This app might be running at the demo server: http://flexx1.zoof.io
"""

from flexx import flx


class Relay(flx.Component):
    """ Global object to relay messages to all participants.
    """

    @flx.emitter
    def create_message(self, name, message):
        return dict(name=name, message=message)

    @flx.emitter
    def new_name(self):
        return {}

# Create global relay
relay = Relay()


class MessageBox(flx.Label):

    CSS = """
    .flx-MessageBox {
        overflow-y:scroll;
        background: #e8e8e8;
        border: 1px solid #444;
        margin: 3px;
    }
    """

    def init(self):
        super().init()
        global window
        self._se = window.document.createElement('div')

    def sanitize(self, text):
        self._se.textContent = text
        text = self._se.innerHTML
        self._se.textContent = ''
        return text

    @flx.action
    def add_message(self, name, msg):
        line = '<i>' + self.sanitize(name) + '</i>: ' + self.sanitize(msg)
        self.set_html(self.html + line + '<br />')


class ChatRoom(flx.PyWidget):
    """ This represents one connection to the chat room.
    """

    def init(self):
        with flx.HBox(title='Flexx chatroom demo'):
            flx.Widget(flex=1)
            with flx.VBox():
                self.name_edit = flx.LineEdit(placeholder_text='your name')
                self.people_label = flx.Label(flex=1, minsize=250)
            with flx.VBox(minsize=450):
                self.messages = MessageBox(flex=1)
                with flx.HBox():
                    self.msg_edit = flx.LineEdit(flex=1,
                                                 placeholder_text='enter message')
                    self.ok = flx.Button(text='Send')
            flx.Widget(flex=1)

        self._update_participants()

    @flx.reaction('ok.pointer_down', 'msg_edit.submit')
    def _send_message(self, *events):
        text = self.msg_edit.text
        if text:
            name = self.name_edit.text or 'anonymous'
            relay.create_message(name, text)
            self.msg_edit.set_text('')

    @relay.reaction('create_message')  # note that we connect to relay
    def _push_info(self, *events):
        for ev in events:
            self.messages.add_message(ev.name, ev.message)

    @flx.reaction('name_edit.user_done')  # tell everyone we changed our name
    def _push_name(self, *events):
        relay.new_name()

    @relay.reaction('new_name')  # check for updated names
    def _new_name(self, *events):
        self._update_participants(self, [])

    @flx.manager.reaction('connections_changed')
    def _update_participants(self, *event):
        if self.session.status:
            # Query the app manager to see who's in the room
            sessions = flx.manager.get_connections(self.session.app_name)
            names = [s.app.name_edit.text for s in sessions]
            del sessions
            text = '<br />%i persons in this chat:<br /><br />' % len(names)
            text += '<br />'.join([name or 'anonymous' for name in sorted(names)])
            self.people_label.set_html(text)

if __name__ == '__main__':
    a = flx.App(ChatRoom)
    a.serve()
    # m = a.launch('firefox')  # for use during development
    flx.start()
