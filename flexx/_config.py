from .util.config import Config

config = Config('flexx', '~appdata/.flexx.cfg',
    log_level=('info', str, 'The log level to use (DEBUG, INFO, WARNING, ERROR)'),
    hostname=('localhost', str, 'The default hostname to serve apps.'),
    port=(0, int, 'The default port to serve apps. Zero means auto-select.'),
    webruntime=('', str, 'The default web runtime to use. Default is xul/browser.'),
    ws_timeout=(20, int, 'If the websocket is idle for this amount of seconds, '
                         'it is closed.'),
    bundle_all=(False, bool, 'Whether to serve all known modules, '
                             'or only the modules that we know are used.'),
    )
