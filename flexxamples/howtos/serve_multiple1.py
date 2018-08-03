"""
Import apps from other example modules, and host these as separate apps
from one process.
"""

from flexx import app

from flexxamples.demos.monitor import Monitor
from flexxamples.demos.chatroom import ChatRoom
from flexxamples.demos.demo import Demo
from flexxamples.demos.colab_painting import ColabPainting


if __name__ == '__main__':
    # This example is setup as a server app
    app.serve(Monitor)
    app.serve(ChatRoom)
    app.serve(ColabPainting)
    app.serve(Demo)
    app.start()
