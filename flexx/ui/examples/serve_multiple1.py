"""
Import apps from other example modules, and host these as separate apps
from one process.
"""

from flexx import app

from flexx.ui.examples.monitor import Monitor
from flexx.ui.examples.chatroom import ChatRoom
from flexx.ui.examples.twente import Twente


if __name__ == '__main__':
    # This example is setup as a server app
    app.serve(Monitor)
    app.serve(ChatRoom)
    app.serve(Twente)
    app.start()
