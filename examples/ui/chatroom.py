""" Simple web app to monitor the CPU usage of the server process.

Requires psutil
"""

import time
import psutil

from flexx import app, ui, react

nsamples = 16


class Room(react.HasSignals):
    
    def __init__(self):
        react.HasSignals.__init__(self)
        self._text = ''
    
    @react.input
    def message(self, msg):
        return msg + '<br />'
        
    # @react.connect('message')
    # def total_text(self, new_txt):
    #     self._text += new_txt + '<br />'
    #     return self._text


room = Room()


@app.serve
class ChatRoom(ui.Widget):
    """ Despite the name, this represents one connection to the chat room.
    """
    
    def init(self):
        with ui.HBox():
            ui.Widget(flex=1)
            self.people = ui.Label(size=(250, 0))
            with ui.VBox():
                self.messages = ui.Label(flex=1, bgcolor='#eee')
                with ui.HBox():
                    self.message = ui.LineEdit(flex=1, placeholder_text='enter message')
                    self.ok = ui.Button(text='Send')
            ui.Widget(flex=1)
    
    @react.connect('ok.mouse_down')
    def _send_message(self, down):
        if down:
            print(self.message.user_text())
            room.message(self.message.text())
            self.message.text('')
    
    @react.connect('room.message')
    def new_text(self, text):
        return text  # proxy to pass total_text to JS
    
    class JS:
        
        @react.connect('new_text')
        def _update_total_text(self, text):
            self.messages.text(self.messages.text() + text)
        

m = app.launch(ChatRoom)  # for use during development
app.start()
