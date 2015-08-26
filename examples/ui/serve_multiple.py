""" Import apps from other example modules, and host these from one
process.
"""

from flexx import app

import cpu_monitor
import chatroom
import twente_temperature

# the cpu monitor and chat room apps are already registered for serving,
# but not the twente_temperature app.
app.serve(twente_temperature.Twente)

if __name__ == '__main__':
    app.start()
