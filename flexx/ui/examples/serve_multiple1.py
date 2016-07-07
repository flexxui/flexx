"""
Import apps from other example modules, and host these as separate apps
from one process.
"""

from flexx import app

from flexx.ui.examples.monitor import Monitor
from flexx.ui.examples.chatroom import ChatRoom
from flexx.ui.examples.demo import Demo
from flexx.ui.examples.colab_painting import ColabPainting


if __name__ == '__main__':
    # This example is setup as a server app
    app.serve(Monitor)
    app.serve(ChatRoom)
    app.serve(ColabPainting)
    app.serve(Demo)
    app.start()
