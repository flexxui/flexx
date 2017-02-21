from .util.config import Config

config = Config('flexx', '~appdata/.flexx.cfg',

        # General
        log_level=('info', str, 'The log level to use (DEBUG, INFO, WARNING, ERROR)'),
        
        # flexx.app
        hostname=('localhost', str, 'The default hostname to serve apps.'),
        port=(0, int, 'The default port to serve apps. Zero means auto-select.'),
        host_whitelist=('', str, 'Comma separated list of allowed <host>:<port> '
                        'values to pass cross-origin checks.'),
        ws_timeout=(20, int, 'If the websocket is idle for this amount of seconds, '
                 'it is closed.'),
        ssl_certfile=('', str, 'The cert file for https server.'),
        ssl_keyfile=('', str, 'The key file for https server.'),
        
        # flexx.webruntime
        webruntime=('', str, 'The default web runtime to use. '
                    'Default is "app or browser".'),
        firefox_exe=('', str, 'The location of the Firefox executable. '
                     'Auto-detect by default.'),
        chrome_exe=('', str, 'The location of the Chrome/Chromium executable. '
                    'Auto-detect by default.'),
        nw_exe=('', str, 'The location of the NW.js executable. '
                'Auto-install by default.'),
        )
