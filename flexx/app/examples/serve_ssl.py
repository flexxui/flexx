"""
Flexx can be configured to use SSL.

This example first creates a self-signed certificate and then uses it to create
a SSL enabled web server (through Tornado ssl_option argument).

Application served through this server is loaded on the browser with 'https'
protocol and its websocket is using 'wss'.
"""

from flexx import app, ui

# generate self-signed certificate for this example
import os

CERTFILE = '/tmp/self-signed.crt'
KEYFILE = '/tmp/self-signed.key'

os.system('openssl req -x509 -nodes -days 1 -batch -newkey rsa:2048 '
          '-keyout %s -out %s' % (KEYFILE, CERTFILE))

# Some very secret Model
class Example(ui.Widget):
    def init(self):
        ui.Button(text='Secret Button')

# configure web server for SSL
app.create_server(ssl_options={'certfile' : CERTFILE,
                               'keyfile' : KEYFILE})

# run application
app.serve(Example, 'Example')
app.run()
