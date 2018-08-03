"""
Flexx can be configured to use SSL.

This example first creates a self-signed certificate and then uses it to create
a SSL enabled web server (through Tornado ssl_option argument).

Application served through this server is loaded on the browser with 'https'
protocol and its websocket is using 'wss'.
"""

from flexx import flx

# generate self-signed certificate for this example
import os

CERTFILE = '/tmp/self-signed.crt'
KEYFILE = '/tmp/self-signed.key'

os.system('openssl req -x509 -nodes -days 1 -batch -newkey rsa:2048 '
          '-keyout %s -out %s' % (KEYFILE, CERTFILE))

# use the self-signed certificate as if specified in normal config
flx.config.ssl_certfile = CERTFILE
flx.config.ssl_keyfile = KEYFILE


# Some very secret Model
class Example(flx.Widget):
    def init(self):
        flx.Button(text='Secret Button')

# run application
flx.serve(Example, 'Example')
flx.start()
