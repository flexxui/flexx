from .util.config import Config

config = Config('flexx', '~appdata/.flexx.cfg',
    hostname=('localhost', str, 'The default port to serve apps.'),
    port=(0, int, 'The default port to serve apps. Zero means auto-select.'),
    webruntime=('', str, 'The default web runtime to use. Default is xul/browser.')
    )
