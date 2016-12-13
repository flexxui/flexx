from .util.config import Config

config = Config('flexx', '~appdata/.flexx.cfg',
                log_level=('info', str, 'The log level to use (DEBUG, INFO, WARNING, ERROR)'),
                hostname=('localhost', str, 'The default hostname to serve apps.'),
                port=(0, int, 'The default port to serve apps. Zero means auto-select.'),
                webruntime=('', str, 'The default web runtime to use. Default is xul/browser.'),
                ws_timeout=(20, int, 'If the websocket is idle for this amount of seconds, '
                         'it is closed.'),
                ssl_certfile=('', str, 'cert file for https server.'),
                ssl_keyfile=('', str, 'key file for https server.'),
                host_whitelist=('', str, 'Comma separated list of allowed <host>:<port> '
                              'values to pass cross-origin checks.'),
                )
