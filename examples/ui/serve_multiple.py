# flake8: noqa
"""
Import apps from other example modules, and host these from one
process.
"""

from flexx import app

import cpu_monitor
import chatroom
import twente_temperature

# Note that all imported apps are already marked for serving.
if __name__ == '__main__':
    app.start()
