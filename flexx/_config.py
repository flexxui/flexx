from .util.config import Config

config = Config('flexx', '~appdata/.flexx.cfg',
                dummy=(0, int, 'Flexx does not have any config options yet')
                )
